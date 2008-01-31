'''
svnUsers.py

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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.parsers.dpCache as dpCache
from core.data.parsers.urlParser import *
from core.data.getResponseType import *
import re
import core.data.constants.severity as severity

class svnUsers(baseGrepPlugin):
    '''
    Grep every response for users of the versioning system.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._regexList = [ re.compile('\$.*?: .*? .*? \d{4}[-/]\d{1,2}[-/]\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}.*? (.*?) (Exp )?\$') ]
        
    def _testResponse(self, request, response):
        
        if isTextOrHtml(response.getHeaders()):
            
            for regex in self._regexList:
                for m in regex.findall( response.getBody() ):
                    v = vuln.vuln()
                    v.setURL( response.getURL() )
                    v.setId( response.id )
                    v.setDesc( 'The URL : '+ response.getURL()  + ' contains a SVN versioning signature with the username: "' + m[0] + '" . ' )
                    v['user'] = m[0]
                    v.setSeverity(severity.LOW)
                    v.setName( 'SVN user disclosure vulnerability' )
                    
                    kb.kb.append( self, 'users', v )
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'svnUsers', 'users' ), None )
    
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
        This plugin greps every page for users of the versioning system. Sometimes the HTML pages are
        versioned using CVS or SVN, if the header of the versioning system is saved as a comment in this page,
        the user that edited the page will be saved on that header and will be added to the knowledgeBase.
        '''
