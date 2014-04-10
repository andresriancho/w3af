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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln


class basic_auth(BruteforcePlugin):
    """
    Bruteforce HTTP basic authentication.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        BruteforcePlugin.__init__(self)

    def audit(self, freq):
        """
        Tries to bruteforce a basic HTTP auth. This is not fast!

        :param freq: A FuzzableRequest
        """
        auth_url_list = [i.get_url().get_domain_path() for i in
                                 kb.kb.get('http_auth_detect', 'auth')]

        domain_path = freq.get_url().get_domain_path()
        if domain_path in auth_url_list and domain_path not in self._already_tested:

                # Save it (we don't want dups!)
                self._already_tested.append(domain_path)

                # Let the user know what we are doing
                msg = 'Starting basic authentication bruteforce on URL: "%s".'
                om.out.information(msg % domain_path)

                up_generator = self._create_user_pass_generator(domain_path)

                self._bruteforce(domain_path, up_generator)

                om.out.information(
                    'No more user/password combinations available.')

    def _brute_worker(self, url, combination):
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
        # If one thread sees that we already bruteforced the access, the rest will
        # simply no-op
        if not self._found or not self._stop_on_first:
            user, passwd = combination

            raw_values = "%s:%s" % (user, passwd)
            auth = 'Basic %s' % base64.b64encode(raw_values).strip()
            headers = Headers([('Authorization', auth)])

            try:
                response = self._uri_opener.GET(url, cache=False, grep=False,
                                                headers=headers)
            except BaseFrameworkException, w3:
                msg = 'Exception while brute-forcing basic authentication,'\
                      ' error message: "%s".'
                om.out.debug(msg % w3)
            else:
                # GET was OK
                if response.get_code() != 401:
                    self._found = True
                    
                    desc = 'Found authentication credentials to: "%s".'\
                           ' A valid user and password combination is: %s/%s .'
                    desc = desc % (url, user, passwd)
                    v = Vuln('Guessable credentials', desc,
                             severity.HIGH, response.id, self.get_name())
                    v.set_url(url)
                    
                    v['user'] = user
                    v['pass'] = passwd
                    v['response'] = response

                    kb.kb.append(self, 'auth', v)
                    om.out.vulnerability(v.get_desc(),
                                         severity=v.get_severity())

    def end(self):
        """
        Configure the main urllib with the newly found credentials.
        """
        for v in kb.kb.get('basic_auth', 'auth'):
            self._uri_opener.settings.set_basic_auth(v.get_url(),
                                                     v['user'],
                                                     v['pass'])

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin bruteforces basic authentication logins.

        Nine configurable parameters exist:
            - usersFile
            - stopOnFirst
            - passwdFile
            - passEqUser
            - useLeetPasswd
            - useSvnUsers
            - useEmails
            - useProfiling
            - profilingNumber

        This plugin will take users from the file pointed by "usersFile", mail
        users found on the site and email addresses (if "useEmails" is set to True)
        and svn users found on the site ( if "useSvnUsers" is set to True ).

        This plugin will take passwords from the file pointed by "passwdFile" and
        the result of the password profiling plugin (if "useProfiling" is set to
        True). The profilingNumber sets the number of results from the password
        profiling plugin to use in the password field.

        The "stopOnFirst" parameter indicates if the bruteforce will stop when
        finding the first valid credentials or not.
        """
