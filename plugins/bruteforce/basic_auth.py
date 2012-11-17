'''
basic_auth.py

Copyright 2006 Andres Riancho

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
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from core.controllers.exceptions import w3afException
from core.data.url.xUrllib import xUrllib


class basic_auth(BruteforcePlugin):
    '''
    Bruteforce HTTP basic authentication.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        BruteforcePlugin.__init__(self)

    def audit(self, freq):
        '''
        Tries to bruteforce a basic HTTP auth. This is not fast!

        @param freq: A FuzzableRequest
        '''
        auth_url_list = [i.getURL().getDomainPath() for i in
                                 kb.kb.get('http_auth_detect', 'auth')]

        domain_path = freq.getURL().getDomainPath()
        if domain_path in auth_url_list and domain_path not in self._already_tested:

                # Save it (we don't want dups!)
                self._already_tested.append(domain_path)

                # Let the user know what we are doing
                msg = 'Starting basic authentication bruteforce on URL: "' + \
                    domain_path + '".'
                om.out.information(msg)

                up_generator = self._create_user_pass_generator(domain_path)

                self._bruteforce(domain_path, up_generator)

                om.out.information(
                    'No more user/password combinations available.')

    def _brute_worker(self, url, combination):
        '''
        Try a user/password combination with HTTP basic authentication against
        a specific URL.

        @param url: A string representation of an URL
        @param combination: A tuple that contains (user,pass)
        '''
        # Remember that this worker is called from a thread which lives in a
        # threadpool. If the worker finds something, it has to let the rest know
        # and the way we do that is by setting self._found.
        #
        # If one thread sees that we already bruteforced the access, the rest will
        # simply no-op
        if not self._found or not self._stop_on_first:
            user, passwd = combination

            #
            # TODO: These four lines make the whole process *very* CPU hungry
            #       since we're creating a new xUrllib() for each user/password
            #       combination! In my test environment I achieve 100% CPU usage
            #
            uri_opener = xUrllib()
            uri_opener.settings.setBasicAuth(url, user, passwd)
            # The next lines replace the uri_opener opener with a new one that has
            # the basic auth settings configured
            uri_opener.settings.build_openers()
            uri_opener._opener = uri_opener.settings.get_custom_opener()

            try:
                response = uri_opener.GET(url, cache=False, grep=False)
            except w3afException, w3:
                msg = 'Exception while bruteforcing basic authentication, error'
                msg += ' message: "%s"'
                om.out.debug(msg % w3)
            else:
                # GET was OK
                if response.getCode() != 401:
                    self._found = True
                    v = vuln.vuln()
                    v.set_id(response.id)
                    v.set_plugin_name(self.get_name())
                    v.setURL(url)
                    v.set_desc('Found authentication credentials to: "' + url +
                               '". A correct user and password combination is: ' + user + '/' + passwd)
                    v['user'] = user
                    v['pass'] = passwd
                    v['response'] = response
                    v.set_severity(severity.HIGH)
                    v.set_name('Guessable credentials')

                    kb.kb.append(self, 'auth', v)
                    om.out.vulnerability(
                        v.get_desc(), severity=v.get_severity())

    def end(self):
        '''
        Configure the main urllib with the newly found credentials.
        '''
        for v in kb.kb.get('basic_auth', 'auth'):
            self._uri_opener.settings.setBasicAuth(v.getURL(),
                                                   v['user'],
                                                   v['pass'])

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
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
        '''
