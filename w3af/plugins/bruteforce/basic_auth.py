"""
basic_auth.py

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
import base64
import time

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.misc.epoch_to_string import epoch_to_string
from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.kb.vuln import Vuln


class basic_auth(BruteforcePlugin):
    """
    Bruteforce HTTP basic authentication.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def audit(self, freq, debugging_id=None):
        """
        Tries to bruteforce a basic HTTP auth. This is not fast!

        :param freq: A FuzzableRequest
        :param debugging_id: The ID to use in the logs to be able to track this
                             call to audit(). Plugins need to send this ID to
                             the ExtendedUrllib to get improved logging.
        """
        auth_url_list = [i.get_url().get_domain_path() for i in
                         kb.kb.get('http_auth_detect', 'auth')]

        domain_path = freq.get_url().get_domain_path()

        if domain_path not in auth_url_list:
            return

        if domain_path in self._already_tested:
            return

        # Save it (we don't want dups!)
        self._already_tested.append(domain_path)

        # Let the user know what we are doing
        msg = 'Starting basic authentication bruteforce on "%s"'
        om.out.information(msg % domain_path)
        start = time.time()

        up_generator = self._create_user_pass_generator(domain_path)

        self._bruteforce(domain_path, up_generator, debugging_id)

        self._configure_credentials_in_opener()

        # Finished!
        took_str = epoch_to_string(start)
        msg = 'Finished basic authentication bruteforce on "%s" (spent %s)'
        args = (domain_path, took_str)
        om.out.information(msg % args)

    def _brute_worker(self, url, combination, debugging_id):
        """
        Try a user/password combination with HTTP basic authentication against
        a specific URL.

        :param url: A string representation of an URL
        :param combination: A tuple that contains (user,pass)
        """
        # Remember that this worker is called from a thread which lives in a
        # threadpool. If the worker finds something, it has to let the rest know
        # and the way we do that is by setting self._found.
        #
        # If one thread sees that we already bruteforced the access, the rest
        # will simply no-op
        if self._found and self._stop_on_first:
            return

        user, passwd = combination

        raw_values = '%s:%s' % (user, passwd)
        auth = 'Basic %s' % base64.b64encode(raw_values).strip()
        headers = Headers([('Authorization', auth)])

        fr = FuzzableRequest(url, headers=headers, method='GET')

        try:
            response = self._uri_opener.send_mutant(fr,
                                                    cache=False,
                                                    grep=False,
                                                    debugging_id=debugging_id)
        except BaseFrameworkException, w3:
            msg = ('Exception raised while brute-forcing basic authentication,'
                   ' error message: "%s".')
            om.out.debug(msg % w3)
            return

        if response.get_code() == 401:
            return

        # Found credentials!
        self._found = True

        password_for_report = self._get_password_for_report(passwd)

        desc = ('Found authentication credentials to: "%s".'
                ' A valid user and password combination is: %s/%s .')
        desc %= (url, user, password_for_report)
        v = Vuln('Guessable credentials', desc,
                 severity.HIGH, response.id, self.get_name())
        v.set_url(url)

        v['user'] = user
        v['pass'] = passwd
        v['response'] = response
        v['request'] = fr

        kb.kb.append(self, 'auth', v)
        om.out.vulnerability(v.get_desc(),
                             severity=v.get_severity())

    def _configure_credentials_in_opener(self):
        """
        Configure the main urllib with the newly found credentials.
        """
        for v in kb.kb.get('basic_auth', 'auth'):
            self._uri_opener.settings.set_basic_auth(v.get_url(),
                                                     v['user'],
                                                     v['pass'])

    def end(self):
        self._configure_credentials_in_opener()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin bruteforces basic authentication endpoints.

        Nine configurable parameters exist:
            - users_file
            - stop_on_first
            - passwd_file
            - pass_eq_user
            - use_leet_password
            - use_svn_users
            - use_emails
            - use_profiling
            - profiling_number

        This plugin will take users from the file pointed by "users_file", mail
        users found on the site and email addresses (if "use_emails" is set to True)
        and svn users found on the site ( if "use_svn_users" is set to True ).

        This plugin will take passwords from the file pointed by "passwd_file" and
        the result of the password profiling plugin (if "use_profiling" is set to
        True). The profiling_number sets the number of results from the password
        profiling plugin to use in the password field.

        The "stop_on_first" parameter indicates if the bruteforce will stop when
        finding the first valid credentials or not.
        """
