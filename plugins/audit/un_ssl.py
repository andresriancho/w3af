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

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.misc.levenshtein import relative_distance_boolean


class un_ssl(AuditPlugin):
    '''
    Find out if secure content can also be fetched using http.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)
        
        # Internal variables
        self._run = True

    def audit(self, freq ):
        '''
        Check if the protocol specified in freq is https and fetch the same URL
        using http. ie:
            - input: https://a/
            - check: http://a/
        
        @param freq: A fuzzable_request
        '''
        if not self._run:
            return
        else:
            self._run = False

            # Define some variables
            initial_url = freq.getURL()
            insecure_url = initial_url.copy()
            secure_url = initial_url.copy()
            
            insecure_url.setProtocol('http')
            insecure_fr = freq.copy()
            insecure_fr.setURL( insecure_url )
            
            secure_url.setProtocol('https')
            secure_fr = freq.copy()
            secure_fr.setURL( secure_url )
            
            try:
                insecure_response = self._uri_opener.send_mutant(insecure_fr, follow_redir=False)
                secure_response = self._uri_opener.send_mutant(secure_fr, follow_redir=False)
            except:
                # No vulnerability to report since one of these threw an error
                # (because there is nothing listening on that port).
                pass
            else:
                if insecure_response.getCode() == secure_response.getCode():
                    
                    if relative_distance_boolean( insecure_response.getBody(),
                                                  secure_response.getBody(),
                                                  0.95 ):
                        v = vuln.vuln( freq )
                        v.setPluginName(self.getName())
                        v.setURL(insecure_response.getURL())
                        v.setName( 'Secure content over insecure channel' )
                        v.setSeverity(severity.MEDIUM)
                        msg = 'Secure content can be accesed using the insecure'
                        msg += ' protocol HTTP. The vulnerable URLs are: "%s" - "%s" .'
                        v.setDesc( msg % (secure_url, insecure_url) )
                        v.setId( [insecure_response.id, secure_response.id] )
                        kb.kb.append( self, 'un_ssl', v )
                        om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin verifies that URL's that are available using HTTPS aren't
        available over an insecure HTTP protocol.

        To detect this, the plugin simply requests "https://abc/a.asp" and
        "http://abc.asp" and if both are equal, a vulnerability is found.
        '''
