"""
advanced.py

Copyright 2011 Andres Riancho

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
from urllib import quote_plus
from urlparse import urljoin
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.handlers.redirect import GET_HEAD_CODES
import w3af.core.data.parsers.document_parser as DocumentParser
from w3af.core.data.parsers.utils.form_id_matcher import FormIDMatcher
from w3af.core.data.dc.factory import dc_from_form_params
class advanced(AuthPlugin):
    """
    Advanced authentication plugin.
    """

    MAX_REDIRECTS = 10

    def __init__(self):
        AuthPlugin.__init__(self)

        self.username = ''
        self.password = ''
        self.username_field = ''
        self.password_field = ''
        self.method = 'POST'
        self.login_url = 'http://host.tld/'
        self.form_matcher = ''
        self.auth_url = ''
        self.check_url = 'http://host.tld/'
        self.check_string = ''
        self._login_error = True
        self.follow_redirects = False
        self.url_encode_params = True

    def login(self):
        """
        Login to the application.
        """
        try:
            return self.do_user_login()
        except BaseFrameworkException, e:
            if self._login_error:
                om.out.error(str(e))
                self._login_error = False
            return False

    def do_user_login(self):
        """
        Send the request to login the user.
        :return: True if the login was successful otherwise raise a
                 BaseFrameworkException
        """
        data = None
        local_login_url = self.auth_url
        om.out.error('login_url: ' + self.login_url)
        # get the original login page and collect forms    
        try:
            response = self._uri_opener.GET(self.login_url,
                                            cache=True)
        except:
            om.out.debug('failed to open login_url')
        else:
            # Do not use parser_cache here, it's not good since CAPTCHA implementations 
            # *might* change the image name for each request of the HTML
            #
            # dp = parser_cache.dpc.get_document_parser_for( response )
            #
            try:
               document_parser = DocumentParser.DocumentParser(response)
            except BaseFrameworkException:
               om.out.debug('failed to parse form page')
            else:
               forms_list = document_parser.get_forms()
               selected_form_params = None
               for form_params in forms_list:
                  om.out.debug("formId: "+form_params.get_form_id().to_json())
                  if form_params.is_login_form() and self.form_matcher == "":
                     selected_form_params = form_params
                     break
                  if self.form_matcher != "":
                     matcher = FormIDMatcher.from_json(self.form_matcher)
                     if form_param.matches(matcher):
                        selected_form_params = form_params
                        break
               if selected_form_params != None: 
                  data_container = dc_from_form_params(selected_form_params)
                  if self.username_field != "":
                     for k, v, p, setter in data_container.iter_setters():
                        if k == self.username_field:
                           setter(self.username)
                  else:
                     data_container.set_login_username(self.username)
                  if self.password_field != "":
                     for k, v, p, setter in data_container.iter_setters():
                        if k == self.password_field:
                           setter(self.password)
                  else:
                     data_container.set_login_password(self.password)
                  data = str(data_container)
                  if local_login_url == '':
                     local_login_url = selected_form_params.get_action()
        if data == None:
           msg = "Can't find the proper login form in the page. You should use the form_matcher parameter properly."
           raise BaseFrameworkException(msg)
       
        # Send the auth HTTP request
        functor = getattr(self._uri_opener, self.method)
        response = functor(local_login_url, data)

        redirect_count = 0

        # follow redirects if the feature is enabled
        while self.follow_redirects and redirect_count < self.MAX_REDIRECTS:

            if response.get_code() not in GET_HEAD_CODES:
                # no redirect received, continue
                break

            # Avoid endless loops
            redirect_count += 1

            response_headers = response.get_headers()
            location_header_value, _ = response_headers.iget('location')
            uri_header_value, _ = response_headers.iget('uri')
            redirect_url = location_header_value or uri_header_value

            redirect_url = response.get_url().url_join(redirect_url)

            msg = 'auth.advanced was redirected to URL: "%s"'
            om.out.debug(msg % redirect_url)

            # on HTTP redirect we can only follow up with GET
            response = self._uri_opener.GET(redirect_url)

        if redirect_count == self.MAX_REDIRECTS:
            msg = ('auth.advanced seems to have entered an endless HTTP'
                   ' redirect loop with %s redirects, the last URL was %s')
            raise BaseFrameworkException(msg % (redirect_count, redirect_url))

        # check if we're logged in
        if not self.is_logged():
            msg = "Can't login into web application as %s"
            raise BaseFrameworkException(msg % self.username)
        else:
            om.out.debug('Login success for %s' % self.username)
            return True

    def _get_data_from_format(self):
        """
        :return: A string with all the information to send to the login URL.
        This string contains the username, password, and all the other
        information that was provided by the user and needs to be transmitted to
        the remote web application.
        """
        trans = quote_plus if self.url_encode_params else lambda x: x

        result = result.replace('%u', trans(self.username_field))
        result = result.replace('%U', trans(self.username))
        result = result.replace('%p', trans(self.password_field))
        result = result.replace('%P', trans(self.password))

        return result

    def logout(self):
        """
        User logout.
        """
        return None

    def is_logged(self):
        """Check user session."""
        try:
            body = self._uri_opener.GET(self.check_url, grep=False).body
            logged_in = self.check_string in body

            msg_yes = 'User "%s" is currently logged into the application'
            msg_no = 'User "%s" is NOT logged into the application'
            msg = msg_yes if logged_in else msg_no
            om.out.debug(msg % self.username)

            return logged_in
        except Exception:
            return False

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        options = [
            ('username',
             self.username,
             'string',
             'Username for using in the authentication process'),

            ('password',
             self.password,
             'string',
             'Password for using in the authentication process'),

            ('username_field',
             self.username_field,
             'string', 'Optional username parameter name (ie. "uname" if the HTML looks'
                       ' like <input type="text" name="uname">...)'),

            ('password_field',
             self.password_field,
             'string', 'Optional password parameter name (ie. "pwd" if the HTML looks'
                       ' like <input type="password" name="pwd">...)'),

            ('auth_url',
             self.auth_url,
             'string',
             'Optional URL where the username and password will be sent using the'
             ' configured request method'),

            ('login_url',
             self.login_url,
             'url',
             'URL where the login form is located.'),

            ('form_matcher',
             self.form_matcher,
             'string',
             'json parameter containing at least one of the following field example { "action": "/login", "inputs": "...", "attributes": "...", "hosted_at_url": "http://host.tld/", "method": "POST"}. This need to match partially with a json view of the form you want to log into. if empty it will try to detect the first login form encountered.' ),
 

            ('check_url',
             self.check_url,
             'url',
             'URL used to verify if the session is still active by looking for'
             ' the check_string.'),

            ('check_string',
             self.check_string,
             'string',
             'String for searching on check_url page to determine if the'
             'current session is active.'),

            ('follow_redirects',
             self.follow_redirects,
             'boolean',
             'Follow HTTP redirects in multi-stage authentication flows'),

            ('method',
             self.method,
             'string',
             'The HTTP method to use'),

            ('url_encode_params',
             self.url_encode_params,
             'boolean',
             'URL-encode configured parameters before applying them to the'
             '"data_format".'),
        ]

        ol = OptionList()
        for o in options:
            ol.add(opt_factory(o[0], o[1], o[3], o[2], help=o[3]))

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using
        the user interface generated by the framework using
        the result of get_options().

        :param options_list: A dict with the options for the plugin.
        :return: No value is returned.
        """
        self.username = options_list['username'].get_value()
        self.password = options_list['password'].get_value()
        self.username_field = options_list['username_field'].get_value()
        self.password_field = options_list['password_field'].get_value()
        self.check_string = options_list['check_string'].get_value()
        self.method = options_list['method'].get_value()
        self.auth_url = options_list['auth_url'].get_value()
        self.login_url = options_list['login_url'].get_value()
        self.form_matcher = options_list['form_matcher'].get_value()
        self.check_url = options_list['check_url'].get_value()
        self.follow_redirects = options_list['follow_redirects'].get_value()
        self.url_encode_params = options_list['url_encode_params'].get_value()

        missing_options = []

        for o in options_list:
            if o.get_value() == '' and o.get_name() not in ["form_matcher", "username_field", "password_field", "auth_url"]:
                missing_options.append(o.get_name())

        if missing_options:
            msg = ("All parameters are required and can't be empty except form_matcher. The"
                   " missing parameters are %s")
            raise BaseFrameworkException(msg % ', '.join(missing_options))

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This authentication plugin can login to web applications with more
        complex authentication schemas where the auth.generic plugin falls
        short. Compared to auth.detailed: it support CSRF protection scheme
        in login forms. If you don't set form_matcher it will try to detect
        automatically the proper form to use. If you don't set the
        username_field and password_field it will try to guess it.

        These configurable parameters exist:
            - username
            - password
            - username_field (optional)
            - password_field (optional)
            - auth_url (optional)
            - method
            - login_url
            - form_matcher (optional)
            - check_url
            - check_string
            - follow_redirects

        Advanced descriptions for each configurable parameter are available in
        the plugin configuration menu.
        """
