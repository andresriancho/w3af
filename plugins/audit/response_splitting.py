'''
response_splitting.py

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
from __future__ import with_statement

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.fuzzer.fuzzer import create_mutants

HEADER_NAME = 'vulnerable073b'
HEADER_VALUE = 'ae5cw3af'


class response_splitting(AuditPlugin):
    '''
    Find response splitting vulnerabilities.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    HEADER_INJECTION_TESTS = ( "w3af\r\n" + HEADER_NAME +": " + HEADER_VALUE,
                               "w3af\r" + HEADER_NAME +": " + HEADER_VALUE,
                               "w3af\n" + HEADER_NAME +": " + HEADER_VALUE )

    # A list of error strings produced by the programming framework
    # when we try to modify a header, and the HTML output is already being 
    # written to the cable, or something similar.
    HEADER_ERRORS = ( 'Header may not contain more than a single header, new line detected' ,
                      'Cannot modify header information - headers already sent')

    def __init__(self):
        AuditPlugin.__init__(self)

    def audit(self, freq ):
        '''
        Tests an URL for response splitting vulnerabilities.
        
        @param freq: A fuzzable_request
        '''
        mutants = create_mutants( freq , self.HEADER_INJECTION_TESTS )
            
        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)
    
    def _analyze_result( self, mutant, response ):
        '''
        Analyze results of the _send_mutant method.
        '''
        #
        #   I will only report the vulnerability once.
        #
        if self._has_no_bug(mutant):
                                        
            # When trying to send a response splitting to php 5.1.2 I get :
            # Header may not contain more than a single header, new line detected
            for error in self.HEADER_ERRORS:
                
                if error in response:
                    msg = 'The variable "' + mutant.getVar() + '" of the URL ' + mutant.getURL()
                    msg += ' modifies the headers of the response, but this error was sent while'
                    msg += ' testing for response splitting: "' + error + '"'
                    
                    i = info.info()
                    i.setPluginName(self.get_name())
                    i.set_desc( msg )
                    i.setVar( mutant.getVar() )
                    i.setURI( mutant.getURI() )
                    i.setDc( mutant.getDc() )
                    i.set_id( response.id )
                    i.set_name( 'Parameter modifies headers' )
                    kb.kb.append( self, 'response_splitting', i )

                    return
                
            if self._header_was_injected( response ):
                v = vuln.vuln( mutant )
                v.setPluginName(self.get_name())
                v.set_desc( 'Response Splitting was found at: ' + mutant.foundAt() )
                v.set_id( response.id )
                v.setSeverity(severity.MEDIUM)
                v.set_name( 'Response splitting vulnerability' )
                kb.kb.append( self, 'response_splitting', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(
               kb.kb.get('response_splitting', 'response_splitting'), 'VAR'
               )
        
    def _header_was_injected( self, response ):
        '''
        This method verifies if a header was successfully injected
        
        @parameter response: The HTTP response where I want to find the injected header.
        @return: True / False
        '''
        # Get the lower case headers
        headers = response.getLowerCaseHeaders()
        
        # Analyze injection
        for header, value in headers.items():
            if HEADER_NAME in header and value.lower() == HEADER_VALUE:
                return True
                
            elif HEADER_NAME in header and value.lower() != HEADER_VALUE:
                msg = 'The vulnerable header was added to the HTTP response, '
                msg += 'but the value is not what w3af expected ('+HEADER_NAME+': '+HEADER_VALUE+')'
                msg += ' Please verify manually.'
                om.out.information(msg)

                i = info.info()
                i.setPluginName(self.get_name())
                i.set_desc( msg )
                i.set_id( response.id )
                i.set_name( 'Parameter modifies headers' )
                kb.kb.append( self, 'response_splitting', i )
                return False
                
        return False

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find response splitting vulnerabilities. 
        
        The detection is done by sending "w3af\\r\\nVulnerable: Yes" to every
        injection point, and reading the response headers searching for a header
        with name "Vulnerable" and value "Yes".
        '''
