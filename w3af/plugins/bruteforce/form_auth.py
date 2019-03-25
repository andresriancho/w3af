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

import time

from copy import deepcopy
from itertools import izip, repeat

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.misc.diff import chunked_diff
from w3af.core.controllers.misc.epoch_to_string import epoch_to_string
from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import BaseFrameworkException


class form_auth(BruteforcePlugin):
    """
    Bruteforce HTML form authentication.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        BruteforcePlugin.__init__(self)

        self._found = set()

    def audit(self, freq, debugging_id=None):
        """
        Tries to bruteforce a form auth. This is slow!

        :param freq: A FuzzableRequest
        :param debugging_id: The ID to use in the logs to be able to track this
                             call to audit(). Plugins need to send this ID to
                             the ExtendedUrllib to get improved logging.
        """
        if freq.get_url() in self._already_tested:
            return

        mutant = form_pointer_factory(freq)
        if not self._is_login_form(mutant):
            # Not a login form, login forms have these fields:
            #   * username/password
            #   * password
            return

        self._already_tested.append(mutant.get_url())

        try:
            session = self._create_new_session(mutant, debugging_id)
        except BaseFrameworkException, bfe:
            msg = 'Failed to create new session during form bruteforce setup: "%s"'
            om.out.debug(msg % bfe)
            return

        try:
            login_failed_bodies = self._id_failed_login_pages(mutant, session, debugging_id)
        except BaseFrameworkException, bfe:
            msg = 'Failed to ID failed login page during form bruteforce setup: "%s"'
            om.out.debug(msg % bfe)
            return

        try:
            self._signature_test(mutant, session, login_failed_bodies, debugging_id)
        except BaseFrameworkException, bfe:
            msg = 'Signature test failed during form bruteforce setup: "%s"'
            om.out.debug(msg % bfe)
            return

        user_token, pass_token = mutant.get_dc().get_login_tokens()

        # Let the user know what we are doing
        msg = 'Found a user login form. The form action is: "%s"'
        om.out.information(msg % mutant.get_url())

        if user_token is not None:
            msg = 'The username field to be used is: "%s"'
            om.out.information(msg % user_token.get_name())

        msg = 'The password field to be used is: "%s"'
        om.out.information(msg % pass_token.get_name())

        msg = 'Starting form authentication bruteforce on URL: "%s"'
        om.out.information(msg % mutant.get_url())

        start = time.time()

        if user_token is not None:
            generator = self._create_user_pass_generator(mutant.get_url())
        else:
            generator = self._create_pass_generator(mutant.get_url())

        self._bruteforce_pool(mutant,
                              login_failed_bodies,
                              generator,
                              session,
                              debugging_id)

        # Report that we've finished.
        took_str = epoch_to_string(start)

        msg = 'Finished bruteforcing "%s" (spent %s)'
        args = (mutant.get_url(), took_str)
        om.out.information(msg % args)

    def _create_new_session(self, mutant, debugging_id):
        """
        Creates a new session in the xurllib. This session will be used
        to send HTTP requests and brute force the login.

        :param mutant: The form mutant
        :return: The session ID (a string)
        """
        session = self._uri_opener.get_new_session()

        # And initialize the session (send a request so that in the response
        # we receive the cookie from the application and save it to the
        # cookiejar)
        self._uri_opener.send_mutant(mutant,
                                     grep=False,
                                     session=session,
                                     debugging_id=debugging_id)

        return session

    def _bruteforce_pool(self, mutant, login_failed_res, generator, session, debugging_id):
        args_iter = izip(repeat(mutant),
                         repeat(login_failed_res),
                         generator,
                         repeat(session),
                         repeat(debugging_id))

        self.worker_pool.map_multi_args(self._brute_worker,
                                        args_iter,
                                        chunksize=100)

    def _bruteforce_test(self, mutant, login_failed_res, generator, session, debugging_id):
        for combination in generator:
            self._brute_worker(mutant, login_failed_res, combination, session, debugging_id)

    def _password_only_login(self, form):
        user_token, pass_token = form.get_login_tokens()

        if user_token is None:
            return True

        return False

    def _fill_form(self, form, username, password):
        """
        Set the username and password fields to the provided params. Handle
        the case where the form only has a password field.

        :param form: The Form instance to brute-force
        :param username: Username value
        :param password: Password value
        :return: The form instance with the username (optional) and password
        """
        user_token, pass_token = form.get_login_tokens()

        # Setup the data_container, remember that we can have password
        # only forms!
        if user_token is not None:
            form.set_login_username(username)

        form.set_login_password(password)
        return form

    def _id_failed_login_pages(self, mutant, session, debugging_id):
        """
        Generate different response bodies that are the result of failed
        authentication.

        Return a list with at least the following response bodies:

            * Two response bodies for failed login using a randomly generated
              username and leaving the password field empty. This is stored in
              a FailedLoginPage instance.

            * Two response bodies for failed login using a randomly generated
              username and password. This is stored in a FailedLoginPage
              instance.
        """
        # The result is going to be stored here
        login_failed_result_list = []

        form = mutant.get_dc()
        self._true_extra_fields(form)

        #
        # Create the FailedLoginPage instance for randomly generated username
        # and password
        #
        random_user_pass = []

        for _ in xrange(2):
            user, password = rand_alnum(8), rand_alnum(8)
            self._fill_form(form, user, password)

            response = self._uri_opener.send_mutant(mutant,
                                                    grep=False,
                                                    session=session,
                                                    debugging_id=debugging_id)

            body = self._clean_body(response, user, password)
            random_user_pass.append(body)

        failed_login_page = FailedLoginPage(random_user_pass[0],
                                            random_user_pass[1])

        login_failed_result_list.append(failed_login_page)

        #
        # Create the FailedLoginPage instance for randomly generated username
        # and empty password
        #
        random_user_empty_pass = []

        for _ in xrange(2):
            user, password = rand_alnum(8), ''
            self._fill_form(form, user, password)

            response = self._uri_opener.send_mutant(mutant,
                                                    grep=False,
                                                    session=session,
                                                    debugging_id=debugging_id)

            body = self._clean_body(response, user, password)
            random_user_empty_pass.append(body)

        failed_login_page = FailedLoginPage(random_user_empty_pass[0],
                                            random_user_empty_pass[1])

        login_failed_result_list.append(failed_login_page)

        return login_failed_result_list

    def _signature_test(self, mutant, session, login_failed_bodies, debugging_id):
        """
        Perform a signature test before starting the brute-force process. This
        test makes sure that the signatures captured in _id_failed_login_pages
        are usable.

        The basic idea is to send more failed login attempts and all should
        be identified as failed logins.

        :param mutant: The mutant that holds the login form
        :param session: The HTTP session / cookies to use in the test
        :param login_failed_bodies: The login failed bodies signatures
        :return: True if success, raises exception on failure
        """
        tests = [(rand_alnum(8), rand_alnum(8)),
                 (rand_alnum(8), '')]

        form = mutant.get_dc()

        for user, passwd in tests:
            self._fill_form(form, user, passwd)

            response = self._uri_opener.send_mutant(mutant,
                                                    grep=False,
                                                    session=session,
                                                    debugging_id=debugging_id)
            body = self._clean_body(response, user, passwd)

            if self._matches_any_failed_page(body, login_failed_bodies):
                continue

            msg = 'Failed to generate a response that matches the failed login page'
            raise BaseFrameworkException(msg)

        return True

    def _matches_any_failed_page(self, resp_body, login_failed_result_list):
        """
        :return: True if the resp_body matches the previously created
                 responses that are stored in login_failed_result_list.
        """
        for failed_login_page in login_failed_result_list:
            if failed_login_page.matches(resp_body):
                return True

        # I'm happy! The response_body *IS NOT* a failed login page.
        return False

    def _is_login_form(self, mutant):
        """
        :return: True if this FuzzableRequest is a login form.
        """
        form = mutant.get_dc()

        if isinstance(form, Form):
            return form.is_login_form()

        return False

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

        for pname, value, path, value_setter in form.iter_setters():
            if pname not in user_pass_fields:
                if not value:
                    value_setter('1')

    def _clean_body(self, http_response, username, password):
        """
        Remove username and password from HTTP response, just in case the
        application included them in the response.

        :param http_response: An HTTP response instance
        :param username: The username to replace
        :param password: The password to replace
        :return: A clean body (string)
        """
        #
        # At some point this method was implemented as follows:
        #
        #   strings_to_replace_list = [username, password]
        #   return get_clean_body_impl(http_response.body, strings_to_replace_list)
        #
        # There is a complex interaction between cleaning the response body
        # and the diff() in FailedLoginPage.matches(). The problem is that the
        # bruteforce plugin will extract usernames and passwords from the HTML
        # thus doing a _clean_body() with username and password will "break"
        # one HTTP response in one way (clean with password A) and another HTTP
        # response in another way (clean with password B) thus making diff()
        # crazy
        #

        return http_response.body

    def _brute_worker(self, mutant, login_failed_result_list, combination, session, debugging_id):
        """
        :param mutant: A Mutant holding a QsMutant of PostDataMutant, created
                       using form_pointer_factory
        :param combination: A tuple with (user, pass) or a pass if this is a
                                password only form.
        """
        if mutant.get_url() in self._found and self._stop_on_first:
            return

        mutant = deepcopy(mutant)
        form = mutant.get_dc()

        if self._password_only_login(form):
            user = 'password-only-form'
            password = combination
        else:
            user, password = combination

        self._true_extra_fields(form)
        self._fill_form(form, user, password)

        resp = self._uri_opener.send_mutant(mutant,
                                            session=session,
                                            grep=False,
                                            debugging_id=debugging_id)

        body = self._clean_body(resp, user, password)

        if self._matches_any_failed_page(body, login_failed_result_list):
            return

        #
        # SUCCESS (most likely)
        #
        # The application is most likely answering with one of these
        # messages (first 3 are examples of errors, last is success):
        #
        #   (f) "The username is valid but the password is invalid"
        #
        #   (f) "Brute-force detected, user blocked"
        #
        #   (f) "Brute-force detected, please complete this CAPTCHA form"
        #
        #   (s) "Welcome Mr. Admin, how can I help?"
        #
        # Let's try to identify if we're in the (f) cases...
        #
        # This needs to be done in a different browser session, the old
        # session is (potentially) already logged in, sending a new
        # authentication request in that session will most likely
        # succeed with a 302 redirect to the user's home page or similar
        #
        new_session = self._create_new_session(mutant, debugging_id)

        password_1 = rand_alnum(8)
        form.set_login_password(password_1)
        verify_resp_1 = self._uri_opener.send_mutant(mutant,
                                                     session=new_session,
                                                     grep=False,
                                                     debugging_id=debugging_id)

        password_2 = rand_alnum(8)
        form.set_login_password(password_2)
        verify_resp_2 = self._uri_opener.send_mutant(mutant,
                                                     session=new_session,
                                                     grep=False,
                                                     debugging_id=debugging_id)

        body_1 = self._clean_body(verify_resp_1, user, password_1)
        body_2 = self._clean_body(verify_resp_2, user, password_2)

        potential_captcha_page = FailedLoginPage(body_1, body_2)
        
        if self._matches_any_failed_page(body, [potential_captcha_page]):
            om.out.debug('The form brute-force plugin detected a response'
                         ' that might indicate that a user exists or CAPTCHA'
                         ' protection is present. Please manually review HTTP'
                         ' response with ID %s.' % verify_resp_2.id)
            return

        #
        # Found a valid username and password!
        #
        freq_url = mutant.get_url()
        self._found.add(freq_url)

        password_for_report = self._get_password_for_report(password)
        user_token, pass_token = form.get_login_tokens()

        if user_token is not None:
            desc = ('Found authentication credentials to: "%s". A correct'
                    ' user and password combination is: %s/%s')
            desc %= (freq_url, user, password_for_report)
        else:
            # There is no user field!
            desc = ('Found authentication credentials to: "%s". The correct'
                    ' password is: "%s".')
            desc %= (freq_url, password_for_report)

        v = Vuln.from_mutant('Guessable credentials', desc, severity.HIGH,
                             resp.id, self.get_name(), mutant)
        v['user'] = user
        v['pass'] = password
        v['response'] = resp
        v['request'] = mutant.get_fuzzable_request()

        kb.kb.append(self, 'auth', v)

        om.out.vulnerability(desc, severity=severity.HIGH)

    def end(self):
        self._found = set()
        self._already_tested = []
        self._already_reported = []


def form_pointer_factory(freq):

    if isinstance(freq.get_uri().querystring, Form):
        return QSMutant(freq)

    return PostDataMutant(freq)


class FailedLoginPage(object):
    def __init__(self, body_a, body_b):
        self.body_a = body_a
        self.body_b = body_b
        self.diff_a_b = None

    def matches(self, query):
        """
        This method is used to check if the `query` HTTP response body matches
        the failed login page instance.

        :param query: An HTTP response body
        :return: True if the `query` response body is equal to the failed login
                 bodies which were received in __init__().
        """
        if self.body_a == query:
            return True

        if self.body_b == query:
            return True

        if not fuzzy_equal(self.body_a, query, 0.60):
            # They are really different, no need to calculate diff()
            return False

        if self.diff_a_b is None:
            self.diff_a_b, _ = chunked_diff(self.body_a, self.body_b)

        _, diff_query_a = chunked_diff(self.body_a, query)

        # Had to add this in order to prevent issues with CSRF tokens, which
        # might be part of the HTTP response body, are random (not removed by
        # clean_body) and will "break" the diff
        if len(diff_query_a) < 64:
            return True

        if fuzzy_equal(self.diff_a_b, diff_query_a, 0.9):
            return True

        return False
