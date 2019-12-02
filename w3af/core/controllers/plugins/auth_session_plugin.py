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
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.kb.info import Info


SESSIONS_FAILED_MSG = '''\
The authentication plugin identified that the user session was lost %i times
(%i%%) during the scan. Scan results might be inaccurate because some HTTP
requests were sent with an invalid application session.

The most common causes and solutions for this issue are:

 * The crawler is following the "Logout" link and mistakenly invalidating the session.
   To solve this issue please add the URL of the "Logout" link to the scanner or
   `web_spider` blacklist.

 * The application is closing the scanner's session when it detects uncommon actions.
   Scans are detected when multiple HTTP 500 errors appear, by doing pattern matching
   if the HTTP requests (WAF) or an elevated number of requests per second is sent.
   To reduce the chances of being detected change the user agent, reduce the number
   of threads and only enable a subset of audit and crawl plugins.
'''


class AuthSessionPlugin(AuthPlugin):
    """
    Subclass AuthPlugin to define common methods which are used by plugins to
    login, verify if the session is active and logout.
    """

    MAX_INVALID_SESSION_PERCENT = 5.0
    MIN_SESSION_COUNT_SAMPLES = 10

    def __init__(self):
        AuthPlugin.__init__(self)

        # The auth consumer calls has_active_session() for the first time without
        # first calling login(), that first time will always be a failure
        self._invalid_sessions_count = -1.0
        self._valid_sessions_count = 0.0
        self._session_failed_http_request_ids = []

        #
        # These need to be overridden in sub-classes using configurable
        # parameters to be defined by the user
        #
        self.username = None
        self.check_url = None
        self.check_string = None

    def has_active_session(self, debugging_id=None):
        """
        Check user session.
        """
        #
        # In some cases the authentication plugin is incorrectly configured and
        # we don't want to keep trying over and over to check for an active session
        # when we know it will fail
        #
        if not self._attempt_login:
            return False

        # Create a new debugging ID for each has_active_session() run unless
        # the caller (usually the login method) specifies otherwise
        self._set_debugging_id(debugging_id)

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

            self._handle_session_active_failure()

            return False

        self._log_session_failed_http_response(http_response)

        body = http_response.get_body()
        logged_in = smart_str_ignore(self.check_string) in smart_str_ignore(body)

        if logged_in:
            self._handle_session_active_success()

            msg = 'User "%s" is currently logged into the application'
            msg %= (self.username,)
            self._log_debug(msg)

        else:
            self._handle_session_active_failure()

            msg = ('User "%s" is NOT logged into the application, the'
                   ' `check_string` was not found in the HTTP response'
                   ' with ID %s.')
            msg %= (self.username, http_response.id)
            self._log_debug(msg)

        return logged_in

    def end(self):
        super(AuthSessionPlugin, self).end()

        if self._should_report_invalid_sessions():
            self._report_invalid_sessions()

    def _handle_session_active_failure(self):
        self._invalid_sessions_count += 1

    def _handle_session_active_success(self):
        self._valid_sessions_count += 1

    def _report_invalid_sessions(self):
        args = (self._invalid_sessions_count,
                self._get_invalid_session_perc())
        desc = SESSIONS_FAILED_MSG % args

        self._log_error(desc)

        i = Info('Unstable application session',
                 desc,
                 self._session_failed_http_request_ids,
                 self.get_name())

        i.set_uri(self._get_main_authentication_url())

        kb.kb.append('authentication', 'error', i)

    def _get_invalid_session_perc(self):
        total_session_checks = self._valid_sessions_count + self._invalid_sessions_count

        if total_session_checks == 0:
            return 0.0

        return (self._invalid_sessions_count / total_session_checks) * 100

    def _should_report_invalid_sessions(self):
        percent_failed_sessions = self._get_invalid_session_perc()

        if not percent_failed_sessions >= self.MAX_INVALID_SESSION_PERCENT:
            return False

        total_session_checks = self._valid_sessions_count + self._invalid_sessions_count

        if total_session_checks < self.MIN_SESSION_COUNT_SAMPLES:
            return False

        return True

    def _log_session_failed_http_response(self, http_response):
        response_saved = self._log_http_response(http_response)

        if response_saved:
            self._session_failed_http_request_ids.append(http_response.id)

        return response_saved
