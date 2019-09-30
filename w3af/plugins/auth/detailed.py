"""
detailed.py

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

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.handlers.redirect import GET_HEAD_CODES


class detailed(AuthPlugin):
    """
    Detailed authentication plugin.
    """

    MAX_REDIRECTS = 10

    def __init__(self):
        AuthPlugin.__init__(self)

        # User configuration
        self.username = ''
        self.password = ''
        self.username_field = ''
        self.password_field = ''
        self.method = 'POST'
        self.data_format = '%u=%U&%p=%P'
        self.auth_url = 'http://host.tld/'
        self.check_url = 'http://host.tld/'
        self.check_string = ''
        self.follow_redirects = False
        self.url_encode_params = True

        # Internal attributes
        self._show_login_error = True
        self._attempt_login = True

    def login(self):
        """
        Login to the application
        """
        #
        # In some cases the authentication plugin is incorrectly configured and
        # we don't want to keep trying over and over to login when we know it
        # will fail
        #
        if not self._attempt_login:
            return False

        #
        # Create a new debugging ID for each login() run
        #
        self._new_debugging_id()
        self._clear_log()

        msg = 'Logging into the application with user: %s' % self.username
        self._log_debug(msg)

        #
        # Send the auth HTTP request
        #
        data = self._get_data_from_format()
        functor = getattr(self._uri_opener, self.method)

        try:
            http_response = functor(self.auth_url,
                                    data,
                                    grep=False,
                                    cache=False,
                                    follow_redirects=self.follow_redirects,
                                    debugging_id=self._debugging_id)
        except Exception, e:
            msg = 'Failed to login to the application because of exception: %s'
            self._log_debug(msg % e)
            return False

        self._log_http_response(http_response)

        #
        # Check if we're logged in
        #
        if not self.has_active_session():
            self._log_info_to_kb()
            return False

        om.out.debug('Login success for %s' % self.username)
        return True

    def logout(self):
        """
        User logout
        """
        return None

    def has_active_session(self):
        """
        Check user session
        """
        # Create a new debugging ID for each has_active_session() run
        self._new_debugging_id()

        msg = 'Checking if session for user %s is active'
        self._log_debug(msg % self.username)

        try:
            http_response = self._uri_opener.GET(self.check_url,
                                                 grep=False,
                                                 cache=False,
                                                 follow_redirects=True,
                                                 debugging_id=self._debugging_id)
        except Exception, e:
            msg = 'Failed to check if session is active because of exception: %s'
            self._log_debug(msg % e)
            return False

        self._log_http_response(http_response)

        body = http_response.get_body()
        logged_in = self.check_string in body

        msg_yes = 'User "%s" is currently logged into the application'
        msg_yes %= (self.username,)

        msg_no = ('User "%s" is NOT logged into the application, the'
                  ' `check_string` was not found in the HTTP response'
                  ' with ID %s.')
        msg_no %= (self.username, http_response.id)

        msg = msg_yes if logged_in else msg_no
        self._log_debug(msg)

        return logged_in

    def _get_data_from_format(self):
        """
        :return: A string with all the information to send to the login URL.
        This string contains the username, password, and all the other
        information that was provided by the user and needs to be transmitted to
        the remote web application.
        """
        trans = quote_plus if self.url_encode_params else lambda x: x

        result = self.data_format
        result = result.replace('%u', trans(self.username_field))
        result = result.replace('%U', trans(self.username))
        result = result.replace('%p', trans(self.password_field))
        result = result.replace('%P', trans(self.password))

        return result

    def _get_main_authentication_url(self):
        return self.auth_url

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
             'string', 'Username parameter name (ie. "uname" if the HTML looks'
                       ' like <input type="text" name="uname">...)'),

            ('password_field',
             self.password_field,
             'string', 'Password parameter name (ie. "pwd" if the HTML looks'
                       ' like <input type="password" name="pwd">...)'),

            ('auth_url',
             self.auth_url,
             'url',
             'URL where the username and password will be sent using the'
             ' configured request method'),

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

            ('data_format',
             self.data_format,
             'string',
             'The format for the POST-data or query string. The following are'
             ' valid formatting values:\n'
             '    - %u for the username parameter name value\n'
             '    - %U for the username value\n'
             '    - %p for the password parameter name value\n'
             '    - %P for the password value\n'),

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
        self.data_format = options_list['data_format'].get_value()
        self.check_string = options_list['check_string'].get_value()
        self.method = options_list['method'].get_value()
        self.auth_url = options_list['auth_url'].get_value()
        self.check_url = options_list['check_url'].get_value()
        self.follow_redirects = options_list['follow_redirects'].get_value()
        self.url_encode_params = options_list['url_encode_params'].get_value()

        missing_options = []

        for o in options_list:
            if o.get_value() == '':
                missing_options.append(o.get_name())

        if missing_options:
            msg = ("All parameters are required and can't be empty. The"
                   " missing parameters are %s")
            raise BaseFrameworkException(msg % ', '.join(missing_options))

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This authentication plugin can login to web applications with more
        complex authentication schemas where the auth.generic plugin falls
        short.

        These configurable parameters exist:
            - username
            - password
            - username_field
            - password_field
            - data_format
            - auth_url
            - method
            - check_url
            - check_string
            - follow_redirects

        Detailed descriptions for each configurable parameter are available in
        the plugin configuration menu.
        """