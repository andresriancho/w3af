'''
un_ssl.py

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
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.misc.levenshtein import relative_distance_boolean
from core.controllers.exceptions import w3afException
from core.data.kb.vuln import Vuln


class un_ssl(AuditPlugin):
    '''
    Find out if secure content can also be fetched using http.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._run = True

    def audit(self, freq):
        '''
        Check if the protocol specified in freq is https and fetch the same URL
        using http. ie:
            - input: https://a/
            - check: http://a/

        @param freq: A FuzzableRequest
        '''
        if not self._run:
            return
        else:
            self._run = False

            # Define some variables
            initial_url = freq.get_url()
            insecure_url = initial_url.copy()
            secure_url = initial_url.copy()

            insecure_url.set_protocol('http')
            insecure_fr = freq.copy()
            insecure_fr.set_url(insecure_url)

            secure_url.set_protocol('https')
            secure_fr = freq.copy()
            secure_fr.set_url(secure_url)

            try:
                insecure_response = self._uri_opener.send_mutant(
                    insecure_fr, follow_redir=False, grep=False)
                secure_response = self._uri_opener.send_mutant(
                    secure_fr, follow_redir=False, grep=False)
            except w3afException:
                # No vulnerability to report since one of these threw an error
                # (because there is nothing listening on that port).
                pass
            else:
                if insecure_response.get_code() == secure_response.get_code()\
                and relative_distance_boolean(insecure_response.get_body(),
                                              secure_response.get_body(),
                                              0.95):
                    desc = 'Secure content can be accesed using the insecure'\
                           ' protocol HTTP. The vulnerable URLs are:'\
                           ' "%s" - "%s" .'
                    desc = desc % (secure_url, insecure_url)
                    
                    response_ids = [insecure_response.id, secure_response.id]
                    
                    v = Vuln('Secure content over insecure channel', desc,
                             severity.MEDIUM, response_ids,
                             self.get_name(), freq)

                    kb.kb.append(self, 'un_ssl', v)
                    
                    om.out.vulnerability(v.get_desc(),
                                         severity=v.get_severity())

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin verifies that URL's that are available using HTTPS aren't
        available over an insecure HTTP protocol.

        To detect this, the plugin simply requests "https://abc/a.asp" and
        "http://abc.asp" and if both are equal, a vulnerability is found.
        '''
