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

from w3af.core.data.dc.form import Form
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ScanMustStopOnUrlError)


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
        if freq.get_url() in self._already_tested:
            return

        if not self._is_login_form(freq):
            return

        self._already_tested.append(freq.get_url())

        user_token, pass_token = freq.get_raw_data().get_login_tokens()

        try:
            login_failed_bodies = self._id_failed_login_page(freq)
        except BaseFrameworkException, bfe:
            msg = 'Unexpected response during form bruteforce setup: "%s"'
            om.out.debug(msg % bfe)
            return

        # Let the user know what we are doing
        om.out.information('Found a form login. The action of the '
                           'form is: "%s".' % freq.get_url())
        if user_token is not None:
            om.out.information('The username field to be used is: "%s".'
                               % user_token.get_name())
        om.out.information('The password field to be used is: "%s".'
                           % pass_token.get_name())
        om.out.information('Starting form authentication bruteforce on URL: "%s".'
                           % freq.get_url())

        if user_token is not None:
            generator = self._create_user_pass_generator(freq.get_url())
        else:
            generator = self._create_pass_generator(freq.get_url())

        self._bruteforce_test(freq, login_failed_bodies, generator)

        # Report that we've finished.
        msg = 'Finished bruteforcing "%s".' % freq.get_url()
        om.out.information(msg)

    def _bruteforce_pool(self, freq, login_failed_res, generator):
        args_iter = izip(repeat(freq), repeat(login_failed_res), generator)
        self.worker_pool.map_multi_args(self._brute_worker, args_iter,
                                        chunksize=100)

    def _bruteforce_test(self, freq, login_failed_res, generator):
        for combination in generator:
            self._brute_worker(freq, login_failed_res, combination)

    def _id_failed_login_page(self, freq):
        """
        Generate TWO different response bodies that are the result of failed
        logins.

        The first result is for logins with filled user and password fields;
        the second one is for a filled user and a blank passwd.
        """
        # The result is going to be stored here
        login_failed_result_list = []

        form = freq.get_raw_data()
        self._true_extra_fields(form)

        user_token, pass_token = form.get_login_tokens()

        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(rand_alnum(8), rand_alnum(8)),
                 (rand_alnum(8), '')]

        for user, passwd in tests:
            # Setup the data_container
            # Remember that we can have password only forms!
            if user_token is not None:
                form.set_login_username(user)

            form.set_login_password(passwd)

            response = self._uri_opener.send_mutant(freq, grep=False)

            # Save it
            body = self.clean_body(response, user, passwd)
            login_failed_result_list.append(body)

        # Now I perform a self test, before starting with the actual
        # bruteforcing. The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(rand_alnum(8), rand_alnum(8)),
                 (rand_alnum(8), '')]

        for user, passwd in tests:
            # Now I do a self test of the result I just created.
            # Remember that we can have password only forms!
            if user_token is not None:
                form.set_login_username(user)

            form.set_login_password(passwd)

            response = self._uri_opener.send_mutant(freq, grep=False)
            body = self.clean_body(response, user, passwd)

            if not self._matches_failed_login(body, login_failed_result_list):
                raise BaseFrameworkException('Failed to generate a response'
                                             'that matches the failed login'
                                             ' page.')

        return login_failed_result_list

    def _matches_failed_login(self, resp_body, login_failed_result_list):
        """
        :return: True if the resp_body matches the previously created
                 responses that are stored in login_failed_result_list.
        """
        for login_failed_result in login_failed_result_list:
            if fuzzy_equal(resp_body, login_failed_result, 0.65):
                return True
        else:
            # I'm happy! The response_body *IS NOT* a failed login page.
            return False

    def _is_login_form(self, freq):
        """
        :return: True if this FuzzableRequest is a login form.
        """
        data_container = freq.get_raw_data()

        if not isinstance(data_container, Form):
            return False

        return data_container.is_login_form()

    def _true_extra_fields(self, form):
        """
        Some login forms have "extra" parameters. In some cases I've seen
        login forms that have an "I agree with the terms and conditions"
        checkbox. If w3af does not set that extra field to "true", even if
        I have the correct username and password combination, it won't
        perform a successful login.

        :return: A data_container that has all fields (other than the username
            and password) set to 1,
        """
        user_token, pass_token = form.get_login_tokens()

        pass_field = pass_token.get_name()
        user_pass_fields = {pass_field}

        if user_token is not None:
            user_pass_fields.add(user_token.get_name())

        for pname, value, value_setter in form.iter_setters():
            if pname not in user_pass_fields:
                if not value:
                    value_setter('1')

    def clean_body(self, http_response, *args):
        """
        Remove all *args from HTTP response body

        :param http_response: An HTTP response instance
        :param args: All the strings I want to remove from the body
        :return: A clean body (string)
        """
        body = http_response.get_body()

        for to_repl in args:
            body = body.replace(to_repl, '')

        return body

    def _brute_worker(self, freq, login_failed_result_list, combination):
        """
        :param freq: A FuzzableRequest
        :param combination: A tuple with (user, pass) or a pass if this is a
                                password only form.
        """
        if freq.get_url() in self._found and self._stop_on_first:
            return

        freq = freq.copy()
        form = freq.get_raw_data()
        self._true_extra_fields(form)

        user_token, pass_token = form.get_login_tokens()

        # Handle password-only forms!
        if user_token is not None:
            user, pwd = combination
            form.set_login_username(user)
            form.set_login_password(pwd)
        else:
            user = 'password-only-form'
            pwd = combination
            form.set_login_password(pwd)

        try:
            resp = self._uri_opener.send_mutant(freq, cookies=False, grep=False)
        except ScanMustStopOnUrlError:
            return

        body = self.clean_body(resp, user, pwd)

        if self._matches_failed_login(body, login_failed_result_list):
            return

        # Ok, this might be a valid combination.
        # Now test with a new invalid password to ensure our
        # previous possible found credentials are valid
        form.set_login_password(rand_alnum(8))

        verif_resp = self._uri_opener.send_mutant(freq,
                                                  cookies=False,
                                                  grep=False)

        body = self.clean_body(verif_resp, user, pwd)

        if self._matches_failed_login(body, login_failed_result_list):
            freq_url = freq.get_url()
            self._found.add(freq_url)

            if user_token is not None:
                desc = ('Found authentication credentials to: "%s". A correct'
                        ' user and password combination is: %s/%s')
                desc %= (freq_url, user, pwd)
            else:
                # There is no user field!
                desc = ('Found authentication credentials to: "%s". The correct'
                        ' password is: "%s".')
                desc %= (freq_url, pwd)

            v = Vuln.from_fr('Guessable credentials', desc, severity.HIGH,
                             resp.id, self.get_name(), freq)
            v['user'] = user
            v['pass'] = pwd
            v['response'] = resp
            v['request'] = freq

            kb.kb.append(self, 'auth', v)

            om.out.vulnerability(desc, severity=severity.HIGH)

    def end(self):
        pass
