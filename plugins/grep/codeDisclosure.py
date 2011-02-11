'''
codeDisclosure.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.misc.is_source_file import is_source_file
from core.data.bloomfilter.pybloom import ScalableBloomFilter


class codeDisclosure(baseGrepPlugin):
    '''
    Grep every page for code disclosure vulnerabilities.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        #   Internal variables
        self._already_added = ScalableBloomFilter()
        self._first_404 = True

    def grep(self, request, response):
        '''
        Plugin entry point, search for the code disclosures.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None

        Init
        >>> import codeDisclosure
        >>> codeDisclosure.is_404 = lambda x: False
        >>> from core.data.url.httpResponse import httpResponse
        >>> from core.data.request.fuzzableRequest import fuzzableRequest
        >>> from core.controllers.misc.temp_dir import create_temp_dir
        >>> o = create_temp_dir()

        Simple test, empty string.
        >>> body = ''
        >>> url = 'http://www.w3af.com/'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> request = fuzzableRequest()
        >>> request.setURL(url)
        >>> request.setMethod('GET')
        >>> c = codeDisclosure.codeDisclosure()
        >>> c.grep(request, response)
        >>> len(kb.kb.getData('codeDisclosure', 'codeDisclosure'))
        0
        
        Disclose some PHP code,
        >>> kb.kb.cleanup()
        >>> body = 'header <? echo "a"; ?> footer'
        >>> url = 'http://www.w3af.com/'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> request = fuzzableRequest()
        >>> request.setURL(url)
        >>> request.setMethod('GET')
        >>> c = codeDisclosure.codeDisclosure()
        >>> c.grep(request, response)
        >>> len(kb.kb.getData('codeDisclosure', 'codeDisclosure'))
        1
        '''
        if response.is_text_or_html() and response.getURL() not in self._already_added:
            
            match, lang  = is_source_file(response.getBody())
            
            if match:
                # Check also for 404
                if not is_404( response ):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURL( response.getURL() )
                    v.setId( response.id )
                    v.setSeverity(severity.LOW)
                    v.setName( lang + ' code disclosure vulnerability' )
                    v.addToHighlight(match.group())
                    msg = 'The URL: "' + v.getURL() + '" has a '+lang+' code disclosure vulnerability.'
                    v.setDesc( msg )
                    kb.kb.append( self, 'codeDisclosure', v )
                    self._already_added.add( response.getURL() )
                
                else:
                    self._first_404 = False
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURL( response.getURL() )
                    v.setId( response.id )
                    v.setSeverity(severity.LOW)
                    v.addToHighlight(match.group())
                    v.setName( lang + ' code disclosure vulnerability in 404 page' )
                    msg = 'The URL: "' + v.getURL() + '" has a '+lang+' code disclosure vulnerability in'
                    msg += ' the customized 404 script.'
                    v.setDesc( msg )
                    kb.kb.append( self, 'codeDisclosure', v )
    
    def setOptions( self, OptionList ):
        '''
        No options to set.
        '''
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print codeDisclosure
        self.printUniq( kb.kb.getData( 'codeDisclosure', 'codeDisclosure' ), 'URL' )
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page in order to find code disclosures. Basically it greps for
        '<?.*?>' and '<%.*%>' using the re module and reports findings.

        Code disclosures are usually generated due to web server misconfigurations, or wierd web
        application "features".
        '''
