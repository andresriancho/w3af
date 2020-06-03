"""
autocomplete_js.py

Copyright 2020 Andres Riancho

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
import Queue
from copy import deepcopy

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import STRING
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.login.find_form.main import FormFinder
from w3af.core.controllers.chrome.login.submit_form.main import FormSubmitter
from w3af.plugins.auth.autocomplete import autocomplete


class autocomplete_js(autocomplete):
    """
    Fill and submit login forms in pages which heavily rely on JavaScript
    """

    def __init__(self):
        autocomplete.__init__(self)

        # default values for autocomplete_js options
        self.username_field_css_selector = ''
        self.login_button_css_selector = ''

        self._login_form = None
        self._http_traffic_queue = None

    def login(self, debugging_id=None):
        """
        Login to the application:
            * HTTP GET `login_form_url`
            * Parse the HTML in `login_form_url` and find the login form
            * Fill the form with the user-configured credentials
            * Submit the form
        """
        #
        # In some cases the authentication plugin is incorrectly configured and
        # we don't want to keep trying over and over to login when we know it
        # will fail
        #
        if not self._attempt_login:
            return False

        # Create a new debugging ID for each login() run
        self._set_debugging_id(debugging_id)
        self._clear_log()

        msg = 'Logging into the application with user: %s' % self.username
        self._log_debug(msg)

        #
        # Perform the login process using a new chrome instance
        #
        chrome = self._get_chrome_instance(load_url=True)

        try:
            login_success = self._do_login(chrome)
        finally:
            # Close chrome
            chrome.terminate()

        if not login_success:
            self._handle_authentication_failure()
            return False

        self._handle_authentication_success()
        return True

    def _handle_authentication_success(self):
        self._login_result_log.append(True)
        #
        # Logging
        #
        args = (self.username,
                self._login_form.get_username_css_selector(),
                self._login_form.get_password_css_selector(),
                self._login_form.get_submit_css_selector())

        msg = 'Login success for username %s with selectors: (username: %s, password: %s, submit: %s)'
        self._log_debug(msg % args)

        #
        # Save the URLs used during the login process to the blacklist in
        # order to prevent audit plugins from sending raw HTTP requests to
        # the login URL and breaking the session
        #
        login_urls = set()

        while not self._http_traffic_queue.empty():
            request, _, _ = self._http_traffic_queue.get_nowait()

            if isinstance(request, FuzzableRequest):
                login_urls.add(request.get_url())

        self._configure_audit_blacklist(*login_urls)

    def _do_login(self, chrome):
        """
        Login to the application in two different scenarios:
            * A login form was previously identified
            * This is the first call to login() and no login form is known

        :param chrome: A chrome instance
        :return: True if login was successful
        """
        if not self._login_form:
            return self._login_and_save_form(chrome)
        else:
            return self._login_using_existing_form(chrome)

    def _login_using_existing_form(self, chrome):
        """
        This method will use the existing form saved in self._login_form to
        perform the login process.

        :param chrome: The chrome instance to use during login
        :return: True if login was successful
        """
        form_submit_strategy = self._find_form_submit_strategy(chrome, self._login_form)
        if form_submit_strategy is None:
            return False
        self._login_form.set_submit_strategy(form_submit_strategy)
        self._log_debug('Identified valid login form: %s' % self._login_form)
        return True

    def _login_and_save_form(self, chrome):
        """
        This method will:

         * Create a chrome instance
         * Use the FormFinder class to yield all existing forms
         * Test which form works
         * Save it

        Subsequent calls will use the saved login form.

        :return: Yield LoginForm (chrome.login.login_form) instances
        """
        for form in self._find_all_login_forms(chrome):

            form_submit_strategy = self._find_form_submit_strategy(chrome, form)

            if form_submit_strategy is None:
                continue

            #
            # At this point the chrome instance has a valid session, because the
            # form submit strategy is only successful when we assert the login
            # was successful
            #
            # If the application session is kept using cookies, then the extended
            # url library also has this session (chrome uses a proxy, the proxy sends
            # the requests via extended url library, cookies are tracked here)
            #
            # Other session handling methods, like special headers or basic auth,
            # are not be supported at this point
            #
            form.set_submit_strategy(form_submit_strategy)

            self._log_debug('Identified valid login form: %s' % form)
            self._login_form = form

            return True

        #
        # We get here when no login form worked. Returning None will disable
        # the auth plugin
        #
        return False

    def _get_chrome_instance(self, load_url=False):
        self._http_traffic_queue = Queue.Queue()

        chrome = InstrumentedChrome(self._uri_opener, self._http_traffic_queue)
        chrome.set_debugging_id(self._debugging_id)

        if load_url:
            self._load_login_form_url(chrome)

        return chrome

    def _load_login_form_url(self, chrome):
        chrome.load_url(self.login_form_url)

        loaded = chrome.wait_for_load()

        if not loaded:
            msg = 'Failed to load %s in chrome for autocomplete_js'
            args = (self.login_form_url,)
            self._log_debug(msg % args)

            return loaded

        return loaded

    def _find_all_login_forms(self, chrome):
        """
         * Create a chrome instance
         * Use the FormFinder class to yield all existing forms
        """
        form_finder = FormFinder(chrome, self._debugging_id)
        css_selectors = {
            'username_input': self.username_field_css_selector,
            'login_button': self.login_button_css_selector,
        }

        for form in form_finder.find_forms(css_selectors):

            msg = 'Found potential login form: %s'
            args = (form,)
            self._log_debug(msg % args)

            yield form

    def _find_form_submit_strategy(self, chrome, form):
        """
        The second challenge with sites which rely heavily on javascript is that
        there might NOT be an <input> with type "submit" which can be clicked
        to submit the form.

        This method attempts to solve that problem by testing different algorithms
        to detect "the login button".

        :param chrome: The chrome instance
        :param form: The LoginForm identified by the previous steps
        :return: True if we were able to submit the login form and the browser
                 obtained a valid session.
        """
        form_submitter = FormSubmitter(chrome,
                                       form,
                                       self.login_form_url,
                                       self.username,
                                       self.password,
                                       self._debugging_id)

        for form_submit_strategy in form_submitter.submit_form():

            if not self.has_active_session(debugging_id=self._debugging_id, chrome=chrome):
                msg = '%s is invalid form submit strategy for %s'
                args = (form_submit_strategy.get_name(), form)
                self._log_debug(msg % args)
                # No need to set the state of the chrome browser back to the
                # login page, that is performed inside the FormSubmitter
                continue

            msg = '%s is a valid form submit strategy for %s'
            args = (form_submit_strategy.get_name(), form)
            self._log_debug(msg % args)

            return form_submit_strategy

        msg = 'No form submit strategy was found to generate a valid session for form %s'
        args = (form,)
        self._log_debug(msg % args)

        return None

    def has_active_session(self, debugging_id=None, chrome=None):
        """
        Check user session with chrome
        :param str debugging_id: string representing debugging id.
        :param InstrumentedChrome chrome: chrome instance passed from outer scope
        to reuse. EDGE CASE EXAMPLE:
        Sometimes we don't want to create new chrome instance. For example
        when we login for the first time to webapp and in _find_form_submit_strategy()
        we just pressed enter in login form. Browser may take some actions under
        the hood like sending XHR to backend API and after receiving response
        setting API token at localStorage. Before token will be saved to localStorage
        it may exist only in webapp's code, so using the same chrome will prevent
        us from performing check without credentials.
        """
        has_active_session = False
        is_new_chrome_instance_created = False
        self._set_debugging_id(debugging_id)
        if not chrome or not chrome.chrome_conn:
            chrome = self._get_chrome_instance(load_url=False)
            is_new_chrome_instance_created = True

        try:
            chrome.load_url(self.check_url)
            chrome.wait_for_load()
            has_active_session = self.check_string in chrome.get_dom()
        finally:
            if is_new_chrome_instance_created:
                chrome.terminate()
            return has_active_session

    def get_options(self):
        """
        :returns OptionList: list of option objects for plugin
        """
        option_list = super(autocomplete_js, self).get_options()
        autocomplete_js_options = [
            (
                'username_field_css_selector',
                self.username_field_css_selector,
                STRING,
                "(Optional) Exact CSS selector which will be used to retrieve "
                "the username input field. When provided the scanner is not going"
                " to try to detect the input field in an automated way"
            ),
            (
                'login_button_css_selector',
                self.login_button_css_selector,
                STRING,
                "(Optional) Exact CSS selector which will be used to retrieve "
                "the login button field. When provided the scanner is not going "
                "to try to detect the login button in an automated way"
            ),
        ]
        for option in autocomplete_js_options:
            option_list.add(opt_factory(
                option[0],
                option[1],
                option[3],
                option[2],
                help=option[3],
            ))
        return option_list

    def set_options(self, options_list):
        options_list_copy = deepcopy(options_list)  # we don't want to touch real option_list
        self.username_field_css_selector = options_list_copy.pop(
            'username_field_css_selector'
        ).get_value()
        self.login_button_css_selector = options_list_copy.pop(
            'login_button_css_selector'
        ).get_value()
        super(autocomplete_js, self).set_options(options_list_copy)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This authentication plugin can login to Web applications which heavily
        rely in JavaScript for handling the authentication form. The plugin
        instruments a real browser to find, complete and submit the login form. 
        
        The plugin loads the `login_form_url` to obtain the login form, automatically
        identifies the inputs where the `username` and `password` should be entered,
        and then submits the form by clicking on the login button. You can specify
        the exact CSS selectors (like ".login > input #password") in
        `username_filed_css_selector` and `login_button_css_selector` to force
        plugin to use those selectors in case when it can't find username field
        or login button automatically.

        The following configurable parameters exist:
            - username
            - password
            - login_form_url
            - check_url
            - check_string
            - username_field_css_selector
            - login_button_css_selector
        """
