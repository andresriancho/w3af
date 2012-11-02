'''
code_disclosure.py

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
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.misc.is_source_file import is_source_file


class code_disclosure(GrepPlugin):
    '''
    Grep every page for code disclosure vulnerabilities.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        
        #   Internal variables
        self._already_added = scalable_bloomfilter()
        self._first_404 = True

    def grep(self, request, response):
        '''
        Plugin entry point, search for the code disclosures.
        
        Unit tests are available at plugins/grep/tests.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html() and response.getURL() not in self._already_added:
            
            match, lang  = is_source_file(response.getBody())
            
            if match:
                # Check also for 404
                if not is_404( response ):
                    v = vuln.vuln()
                    v.setPluginName(self.get_name())
                    v.setURL( response.getURL() )
                    v.set_id( response.id )
                    v.setSeverity(severity.LOW)
                    v.set_name( lang + ' code disclosure vulnerability' )
                    v.addToHighlight(match.group())
                    fmt = 'The URL: "%s" has a %s code disclosure vulnerability.'
                    v.set_desc( fmt % (v.getURL(), lang) )
                    kb.kb.append( self, 'code_disclosure', v )
                    self._already_added.add( response.getURL() )
                
                else:
                    self._first_404 = False
                    v = vuln.vuln()
                    v.setPluginName(self.get_name())
                    v.setURL( response.getURL() )
                    v.set_id( response.id )
                    v.setSeverity(severity.LOW)
                    v.addToHighlight(match.group())
                    v.set_name( lang + ' code disclosure vulnerability in 404 page' )
                    fmt = 'The URL: "%s" has a %s code disclosure vulnerability'\
                          ' in the customized 404 script.'
                    v.set_desc( fmt % (v.getURL(), lang) )
                    kb.kb.append( self, 'code_disclosure', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print code_disclosure
        self.print_uniq( kb.kb.get( 'code_disclosure', 'code_disclosure' ), 'URL' )
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page in order to find code disclosures. Basically
        it greps for '<?.*?>' and '<%.*%>' using the re module and reports
        findings.

        Code disclosures are usually generated due to web server misconfigurations,
        or wierd web application "features".
        '''
