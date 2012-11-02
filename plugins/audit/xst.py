'''
xst.py

Copyright 2007 Andres Riancho

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
import re

import core.controllers.outputManager as om
import core.data.kb.vuln as vuln
import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.dc.headers import Headers


class xst(AuditPlugin):
    '''
    Find Cross Site Tracing vulnerabilities. 

    @author: Josh Summitt (ascetik@gmail.com)
    @author: Andres Riancho (andres@gmail.com) - Rewrite 27 Jul 2012
    '''

    def __init__(self):
        AuditPlugin.__init__(self)
        
        # Internal variables
        self._exec = True

    def audit(self, freq ):
        '''
        Verify xst vulns by sending a TRACE request and analyzing the response.
        '''
    
        if not self._exec:
            # Do nothing
            return
        else:
            # Only run once
            self._exec = False  
            
            uri = freq.getURL().getDomainPath()
            method = 'TRACE'
            headers = Headers()
            headers['FakeHeader'] = 'XST'
            fr = FuzzableRequest(uri,
                                 method=method,
                                 headers=headers
                                 )

            # send the request to the server and receive the response
            response = self._uri_opener.send_mutant(fr)

            # create a regex to test the response. 
            regex = re.compile("FakeHeader: *?XST", re.IGNORECASE)
            if re.search(regex, response.getBody()):
                # If vulnerable record it. This will now become visible on the KB Browser
                v = vuln.vuln( freq )
                v.setPluginName(self.get_name())
                v.set_id( response.id )
                v.setSeverity(severity.LOW)
                v.set_name( 'Cross site tracing vulnerability' )
                msg = 'The web server at "'+ response.getURL() +'" is vulnerable to'
                msg += ' Cross Site Tracing.'
                v.set_desc( msg )
                om.out.vulnerability( v.get_desc(), severity=v.getSeverity() )
                kb.kb.append( self, 'xst', v )
            
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds the Cross Site Tracing (XST) vulnerability.
        
        No configurable paramaters are available.
            
        The TRACE method echos back requests sent to it. This plugin sends a 
        TRACE request to the server and if the request is echoed back then XST 
        is confirmed.
        '''

