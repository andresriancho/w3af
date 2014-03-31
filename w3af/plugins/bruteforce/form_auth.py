"""
form_auth.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
from __future__ import with_statement

from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException, ScanMustStopOnUrlError
from w3af.core.controllers.misc.levenshtein import relative_distance_ge
from w3af.core.data.dc import form
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.kb.vuln import Vuln


class form_auth(BruteforcePlugin):
    """
    Bruteforce HTML form authentication.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        BruteforcePlugin.__init__(self)

        self._found = set()

    def audit(self, freq):
        """
        Tries to bruteforce a form auth. This aint fast!

        :param freq: A FuzzableRequest
        """
        freq_url = freq.get_url()

        if self._is_login_form(freq) and freq_url not in self._already_tested:

            self._already_tested.append(freq_url)

            user_field, passwd_field = self._get_login_field_names(freq)
            login_failed_result_list = self._id_failed_login_page(freq,
                                                                  user_field,
                                                                  passwd_field)

            # Let the user know what we are doing
            om.out.information('Found a form login. The action of the '
                               'form is: "%s".' % freq_url)
            if user_field is not None:
                om.out.information('The username field to be used is: '
                                   '"%s".' % user_field)
            om.out.information('The password field to be used is: "%s".'
                               % passwd_field)
            om.out.information('Starting form authentication bruteforce'
                               ' on URL: "%s".' % freq_url)

            if user_field is not None:
                generator = self._create_user_pass_generator(freq_url)
            else:
                generator = self._create_pass_generator(freq_url)

            self._bruteforce_test(freq, user_field, passwd_field,
                                  login_failed_result_list, generator)

            # Report that we've finished.
            msg = 'Finished bruteforcing "%s".' % freq_url
            om.out.information(msg)

    def _bruteforce(self, url, user_field, passwd_field,
                    login_failed_result_list, generator):
        args_iter = izip(repeat(url), repeat(user_field), repeat(passwd_field),
                         repeat(login_failed_result_list), generator)
        self.worker_pool.map_multi_args(
            self._brute_worker, args_iter, chunksize=100)

    def _bruteforce_test(self, url, user_field, passwd_field,
                         login_failed_result_list, generator):
        for combination in generator:
            self._brute_worker(url, user_field, passwd_field,
                               login_failed_result_list, combination)

    def _id_failed_login_page(self, freq, user_field, passwd_field):
        """
        Generate TWO different response bodies that are the result of failed
        logins.

        The first result is for logins with filled user and password fields;
        the second one is for a filled user and a blank passwd.
        """
        # The result is going to be stored here
        login_failed_result_list = []

        data_container = freq.get_dc()
        data_container = self._true_extra_fields(
            data_container, user_field, passwd_field)

        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(rand_alnum(8), rand_alnum(8)),
                 (rand_alnum(8), '')]

        for user, passwd in tests:
            # Setup the data_container
            # Remember that we can have password only forms!
            if user_field is not None:
                data_container[user_field][0] = user
            data_container[passwd_field][0] = passwd
            freq.set_dc(data_container)

            response = self._uri_opener.send_mutant(freq, grep=False)

            body = response.get_body()
            body = body.replace(user, '')
            body = body.replace(passwd, '')

            # Save it
            login_failed_result_list.append(body)

        # Now I perform a self test, before starting with the actual bruteforcing
        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(rand_alnum(8), rand_alnum(8)),
                 (rand_alnum(8), '')]

        for user, passwd in tests:
            # Now I do a self test of the result I just created.
            #   Remember that we can have password only forms!
            if user_field is not None:
                data_container[user_field][0] = user
            data_container[passwd_field][0] = passwd
            freq.set_dc(data_container)
            response = self._uri_opener.send_mutant(freq, grep=False)

            body = response.get_body()
            body = body.replace(user, '')
            body = body.replace(passwd, '')

            if not self._matches_failed_login(body, login_failed_result_list):
                raise BaseFrameworkException('Failed to generate a response that '
                                    'matches the failed login page.')

        return login_failed_result_list

    def _matches_failed_login(self, resp_body, login_failed_result_list):
        """
        :return: True if the resp_body matches the previously created
                 responses that are stored in login_failed_result_list.
        """
        for login_failed_result in login_failed_result_list:
            if relative_distance_ge(resp_body, login_failed_result, 0.65):
                return True
        else:
            # I'm happy! The response_body *IS NOT* a failed login page.
            return False

    def _is_login_form(self, freq):
        """
        :return: True if this FuzzableRequest is a loginForm.
        """
        passwd = text = other = 0
        data_container = freq.get_dc()

        if isinstance(data_container, form.Form):

            for parameter_name in data_container:

                if data_container.get_type(parameter_name).lower() == 'password':
                    passwd += 1
                elif data_container.get_type(parameter_name).lower() == 'text':
                    text += 1
                else:
                    other += 1

            #
            #   These are the ones we support
            #
            if text == 1 and passwd == 1:
                return True
            elif text == 0 and passwd == 1:
                msg = 'Identified a form with a password field and no username'\
                      ' field: "%s".'
                om.out.information(msg % freq.get_url())
                return True

            #
            #   These we don't
            #
            elif passwd == 2:
                om.out.information(freq.get_url() + ' is a registration form.')
            elif passwd == 3:
                om.out.information(
                    freq.get_url() + ' is a password change form.')
            return False

    def _get_login_field_names(self, freq):
        """
        :return: The names of the form fields where to input the user and the
            password. Please remember that maybe user_parameter might be None,
            since we support password only login forms.
        """
        data_container = freq.get_dc()
        passwd_parameter = None
        user_parameter = None

        for parameter_name in data_container:

            if data_container.get_type(parameter_name).lower() == 'password':
                passwd_parameter = parameter_name

            elif data_container.get_type(parameter_name).lower() == 'text':
                user_parameter = parameter_name

        return user_parameter, passwd_parameter

    def _true_extra_fields(self, data_container, user_field, passwd_field):
        """
        Some login forms have "extra" parameters. In some cases I've seen
        login forms that have an "I agree with the terms and conditions"
        checkbox. If w3af does not set that extra field to "true", even if
        I have the correct username and password combination, it won't
        perform a successful login.

        :return: A data_container that has all fields (other than the username
            and password) set to 1,
        """
        for parameter_name in data_container:
            if parameter_name not in (user_field, passwd_field):
                for element_index, element_value in enumerate(data_container[parameter_name]):
                    if not element_value:
                        data_container[parameter_name][element_index] = '1'
        return data_container

    def _brute_worker(self, freq, user_field, passwd_field,
                      login_failed_result_list, combination):
        """
        :param freq: A FuzzableRequest
        :param combination: A tuple with (user, pass) or a pass if this is a
                                password only form.
        """
        if freq.get_url() not in self._found or not self._stop_on_first:
            freq = freq.copy()
            data_container = freq.get_dc()
            data_container = self._true_extra_fields(
                data_container, user_field, passwd_field)

            # Handle password-only forms!
            if user_field is not None:
                user, pwd = combination
                data_container[user_field][0] = user
                data_container[passwd_field][0] = pwd
            else:
                user = 'password-only-form'
                pwd = combination
                data_container[passwd_field][0] = pwd

            freq.set_dc(data_container)

            try:
                resp = self._uri_opener.send_mutant(freq, cookies=False,
                                                    grep=False)
            except ScanMustStopOnUrlError:
                return
            else:
                body = resp.get_body()
                body = body.replace(user, '').replace(pwd, '')

                if self._matches_failed_login(body, login_failed_result_list):
                    return
                
                # Ok, this might be a valid combination.
                # Now test with a new invalid password to ensure our
                # previous possible found credentials are valid
                data_container[passwd_field][0] = rand_alnum(8)
                freq.set_dc(data_container)
                verif_resp = self._uri_opener.send_mutant(freq,
                                                          cookies=False,
                                                          grep=False)
                body = verif_resp.get_body()
                body = body.replace(user, '').replace(pwd, '')

                if self._matches_failed_login(body, login_failed_result_list):
                    freq_url = freq.get_url()
                    self._found.add(freq_url)
                    
                    if user_field is not None:
                        desc = ('Found authentication credentials to: '
                                '"%s". A correct user and password combination'
                                ' is: %s/%s' % (freq_url, user, pwd))
                    else:
                        # There is no user field!
                        desc = ('Found authentication credentials to: '
                                '"%s". The correct password is: "%s".'
                                % (freq_url, pwd))
                        
                    v = Vuln.from_fr('Guessable credentials', desc,
                                     severity.HIGH, resp.id,
                                     self.get_name(), freq)
                    v['user'] = user
                    v['pass'] = pwd
                    v['response'] = resp

                    kb.kb.append(self, 'auth', v)

                    om.out.vulnerability(desc, severity=severity.HIGH)
                    return

    def end(self):
        pass
