'''
preg_replace.py

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

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.fuzzer.fuzzer import create_mutants
from core.data.esmre.multi_in import multi_in


class preg_replace(AuditPlugin):
    '''
    Find unsafe usage of PHPs preg_replace.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    PREG_PAYLOAD = ['a' + ')/' * 100, ]
    PREG_ERRORS = ( 'Compilation failed: unmatched parentheses at offset',
                    '<b>Warning</b>:  preg_replace() [<a',
                    'Warning: preg_replace(): ' )

    _multi_in = multi_in( PREG_ERRORS )
    
    
    def __init__(self):
        AuditPlugin.__init__(self)
        
    def audit(self, freq ):
        '''
        Tests an URL for unsafe usage of PHP's preg_replace.
        
        @param freq: A FuzzableRequest
        '''
        # First I check If I get the error message from php
        orig_resp = self._uri_opener.send_mutant(freq)
        mutants = create_mutants( freq , self.PREG_PAYLOAD , orig_resp=orig_resp )
        
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
            
            for preg_error_string in self._find_preg_error( response ):
                if preg_error_string not in mutant.get_original_response_body():
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.get_name())
                    v.set_id( response.id )
                    v.set_severity(severity.HIGH)
                    v.set_name( 'Unsafe usage of preg_replace' )
                    v.set_desc( 'Unsafe usage of preg_replace was found at: ' + mutant.found_at() )
                    v.addToHighlight( preg_error_string )
                    kb.kb.append_uniq( self, 'preg_replace', v )
                    break
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'preg_replace', 'preg_replace' ), 'VAR' )
    
    def _find_preg_error( self, response ):
        '''
        This method searches for preg_replace errors in html's.
        
        @param response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for error_match in self._multi_in.query( response.body ):        
            msg = 'An unsafe usage of preg_replace() function was found, the error that was'
            msg += ' sent by the web application is (only a fragment is shown): "'
            msg += error_match + '" ; and was found'
            msg += ' in the response with id ' + str(response.id) + '.'
            
            om.out.information(msg)
            res.append(error_match)
        return res

    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before
                 the current one.
        '''
        return ['grep.error_500']

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find preg_replace vulnerabilities. This PHP function
        is vulnerable when the user can control the regular expression or the
        content of the string being analyzed and the regular expression has the
        'e' modifier.
        
        Right now this plugin will only find preg_replace vulnerabilities when
        PHP is configured to show errors, but a new version will find "blind"
        preg_replace errors.
        '''
