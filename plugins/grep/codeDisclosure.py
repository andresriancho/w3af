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
import core.data.parsers.urlParser as uparser
from core.data.getResponseType import *
import re
import core.data.constants.severity as severity

class codeDisclosure(baseGrepPlugin):
    '''
    Grep every page for code disclosure bugs.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        # This regex means: "find all tags that are of the form <? something ?> but if that something
        # is "xml .*" ignore it completely. This is to remove the false positive in the detection of code disclosure
        # that is added when the web application uses something like
        # <?xml version="1.0" encoding="UTF-8"?>
        # This was added to fix bug #1989056
        php = re.compile( '<\?(?! *xml).*\?>' ,re.IGNORECASE | re.DOTALL)
        # The rest of the regex are ok, because this patterns aren't used in html / xhtml
        asp = re.compile( '<%.*%>' ,re.IGNORECASE | re.DOTALL)
        jsp = re.compile( '<%.*%>' ,re.IGNORECASE | re.DOTALL)
        jsp2 = re.compile( '<jsp:.*>' ,re.IGNORECASE | re.DOTALL)
        
        self._regexs = []
        self._regexs.append( (php, 'PHP') )
        self._regexs.append( (asp, 'ASP') )
        self._regexs.append( (jsp, 'JSP') )
        self._regexs.append( (jsp2, 'JSP') )
        
        self._alreadyAdded = []

    def _testResponse(self, request, response):
        
        if response.is_text_or_html() and response.getURL() not in self._alreadyAdded:
            
            for regex, lang in self._regexs:
                res = regex.search( response.getBody() )
                if res:
                    v = vuln.vuln()
                    v.setURL( response.getURL() )
                    v.setId( response.id )
                    v.setSeverity(severity.LOW)
                    v.setName( 'Code disclosure vulnerability' )
                    v.setDesc( "The URL: " + v.getURL() + " has a code disclosure vulnerability." )
                    kb.kb.append( self, 'codeDisclosure', v )
                    self._alreadyAdded.append( response.getURL() )
    
    def setOptions( self, OptionList ):
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
        '''
