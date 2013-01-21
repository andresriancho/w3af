'''
detailed.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import core.controllers.output_manager as om

from core.controllers.plugins.auth_plugin import AuthPlugin
from core.controllers.exceptions import w3afException

from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList


class detailed(AuthPlugin):
    '''Detailed authentication plugin.'''

    def __init__(self):
        AuthPlugin.__init__(self)

        self.username = ''
        self.password = ''
        self.username_field = ''
        self.password_field = ''
        self.method = 'POST'
        self.data_format = '%u=%U&%p=%P'
        self.auth_url = 'http://host.tld/'
        self.check_url = 'http://host.tld/'
        self.check_string = ''
        self._login_error = True

    def login(self):
        '''
        Login to the application.
        '''

        msg = 'Logging into the application using %s/%s' % (self.username,
                                                            self.password)
        om.out.debug(msg)

        data = self._get_data_from_format()

        try:
            functor = getattr(self._uri_opener, self.method)

            # TODO Why we don't use HTTPPostDataRequest here?
            functor(self.auth_url, data)

            if not self.is_logged():
                raise Exception("Can't login into web application as %s/%s"
                                % (self.username, self.password))
            else:
                om.out.debug('Login success for %s/%s' % (
                    self.username, self.password))
                return True
        except Exception, e:
            if self._login_error:
                om.out.error(str(e))
                self._login_error = False
            return False

    def _get_data_from_format(self):
        '''
        @return: A string with all the information to send to the login URL.
        This string contains the username, password, and all the other information
        that was provided by the user and needs to be transmitted to the remote
        web application.
        '''
        result = self.data_format
        result = result.replace('%u', self.username_field)
        result = result.replace('%U', self.username)
        result = result.replace('%p', self.password_field)
        result = result.replace('%P', self.password)
        return result

    def logout(self):
        '''User login.'''
        return None

    def is_logged(self):
        '''Check user session.'''
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
        '''
        @return: A list of option objects for this plugin.
        '''
        options = [
            ('username', self.username, 'string',
             'Username for using in the authentication'),
            ('password', self.password, 'string',
             'Password for using in the authentication'),
            ('username_field', self.username_field,
             'string', 'Username HTML field name'),
            ('password_field', self.password_field,
             'string', 'Password HTML field name'),
            ('data_format', self.data_format, 'string',
             'The format for the POST-data or query string'),
            ('auth_url', self.auth_url, 'url',
             'Auth URL - URL for POSTing the authentication information'),
            ('method', self.method, 'string', 'The HTTP method to use'),
            ('check_url', self.check_url, 'url',
             'Check session URL - URL in which response body check_string will be searched'),
            ('check_string', self.check_string, 'string',
             'String for searching on check_url page to determine if user\
                    is logged in the web application'),
        ]
        ol = OptionList()
        for o in options:
            ol.add(opt_factory(o[0], o[1], o[3], o[2]))
        return ol

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using
        the user interface generated by the framework using
        the result of get_options().

        @param options_list: A dict with the options for the plugin.
        @return: No value is returned.
        '''
        self.username = options_list['username'].get_value()
        self.password = options_list['password'].get_value()
        self.username_field = options_list['username_field'].get_value()
        self.password_field = options_list['password_field'].get_value()
        self.data_format = options_list['data_format'].get_value()
        self.check_string = options_list['check_string'].get_value()
        self.method = options_list['method'].get_value()
        self.auth_url = options_list['auth_url'].get_value()
        self.check_url = options_list['check_url'].get_value()

        for o in options_list:
            if not o.get_value():
                msg = "All parameters are required and can't be empty."
                raise w3afException(msg)

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This authentication plugin can login to web application with more detailed
        and complex authentication schemas where the generic plugin does not work.

        Nine configurable parameters exist:
            - username
            - password
            - username_field
            - password_field
            - data_format
            - auth_url
            - method
            - check_url
            - check_string
        '''
