"""
generic.py

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
from urllib import urlencode

import w3af.core.controllers.output_manager as om

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.plugins.auth_session_plugin import AuthSessionPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException


class generic(AuthSessionPlugin):
    """
    Generic authentication plugin
    """

    def __init__(self):
        AuthSessionPlugin.__init__(self)

        # User configuration
        self.username = ''
        self.password = ''
        self.username_field = ''
        self.password_field = ''
        self.auth_url = 'http://host.tld/'
        self.check_url = 'http://host.tld/'
        self.check_string = ''

    def login(self, debugging_id=None):
        """
        Login to the application.
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
        self._set_debugging_id(debugging_id)
        self._clear_log()
        self._configure_audit_blacklist(self.auth_url)

        msg = 'Logging into the application using %s' % self.username
        om.out.debug(msg)

        #
        # Send the auth HTTP request
        #
        data = urlencode({self.username_field: self.username,
                          self.password_field: self.password})

        try:
            http_response = self._uri_opener.POST(self.auth_url,
                                                  data=data,
                                                  grep=False,
                                                  cache=False,
                                                  follow_redirects=True,
                                                  debugging_id=self._debugging_id)
        except Exception, e:
            self._handle_authentication_failure()

            msg = 'Failed to login to the application because of exception: %s'
            self._log_debug(msg % e)
            return False

        self._log_http_response(http_response)

        #
        # Check if we're logged in
        #
        if self.has_active_session(debugging_id=debugging_id):
            self._handle_authentication_success()
            return True

        self._handle_authentication_failure()
        return False

    def logout(self):
        """
        User logout
        """
        return None

    def _handle_authentication_success(self):
        super(generic, self)._handle_authentication_success()
        self._log_debug('Login success for %s' % self.username)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        options = [
            ('username', self.username, 'string',
             'Username for using in the authentication process'),

            ('password', self.password, 'string',
             'Password for using in the authentication process'),

            ('username_field', self.username_field,
             'string', 'Username parameter name (ie. "uname" if the HTML looks'
                       ' like <input type="text" name="uname">...)'),

            ('password_field', self.password_field,
             'string', 'Password parameter name (ie. "pwd" if the HTML looks'
                       ' like <input type="password" name="pwd">...)'),

            ('auth_url', self.auth_url, 'url',
             'URL where the username and password will be sent using a POST'
             ' request'),

            ('check_url', self.check_url, 'url',
             'URL used to verify if the session is still active by looking for'
             ' the check_string.'),

            ('check_string', self.check_string, 'string',
             'String for searching on check_url page to determine if the'
             'current session is active.'),
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
        self.auth_url = options_list['auth_url'].get_value()
        self.check_url = options_list['check_url'].get_value()

        missing_options = []

        for o in options_list:
            if not o.get_value():
                missing_options.append(o.get_name())

        if missing_options:
            msg = ('All plugin configuration parameters are required.'
                   ' The missing parameters are: %s')
            raise BaseFrameworkException(msg % ', '.join(missing_options))

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This authentication plugin can login to Web applications which use
        common authentication schemes.

        Seven configurable parameters exist:
            - username
            - password
            - username_field
            - password_field
            - auth_url
            - check_url
            - check_string
        """
