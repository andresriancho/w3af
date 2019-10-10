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
from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException


class generic(AuthPlugin):
    """
    Generic authentication plugin
    """

    def __init__(self):
        AuthPlugin.__init__(self)

        # User configuration
        self.username = ''
        self.password = ''
        self.username_field = ''
        self.password_field = ''
        self.auth_url = 'http://host.tld/'
        self.check_url = 'http://host.tld/'
        self.check_string = ''

        # Internal attributes
        self._attempt_login = True

    def login(self):
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
        self._new_debugging_id()
        self._clear_log()

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
            msg = ("All parameters are required and can't be empty. The"
                   " missing parameters are %s")
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
