"""
auth_session_plugin.py

Copyright 2019 Andres Riancho

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
from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.data.misc.encoding import smart_str_ignore


class AuthSessionPlugin(AuthPlugin):
    """
    Subclass AuthPlugin to define common methods which are used by plugins to
    login, verify if the session is active and logout.
    """
    def __init__(self):
        AuthPlugin.__init__(self)

        #
        # These need to be overridden in sub-classes using configurable
        # parameters to be defined by the user
        #
        self.username = None
        self.check_url = None
        self.check_string = None

    def has_active_session(self):
        """
        Check user session.
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
        logged_in = smart_str_ignore(self.check_string) in smart_str_ignore(body)

        msg_yes = 'User "%s" is currently logged into the application'
        msg_yes %= (self.username,)

        msg_no = ('User "%s" is NOT logged into the application, the'
                  ' `check_string` was not found in the HTTP response'
                  ' with ID %s.')
        msg_no %= (self.username, http_response.id)

        msg = msg_yes if logged_in else msg_no
        self._log_debug(msg)

        return logged_in
