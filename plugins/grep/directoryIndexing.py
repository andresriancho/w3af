'''
directoryIndexing.py

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

import core.data.parsers.htmlParser as htmlParser
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.parsers.urlParser import *
from core.data.getResponseType import *
import core.data.constants.severity as severity
import re

class directoryIndexing(baseGrepPlugin):
    '''
    Grep every response for directory indexing problems.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

    def _testResponse(self, request, response):

        if isTextOrHtml(response.getHeaders()):
            htmlString = response.getBody()
            for directoryIndexingString in self._getdirectoryIndexingStrings():
                if re.search( directoryIndexingString, htmlString ):
                    v = vuln.vuln()
                    v.setURL( response.getURL() )
                    v.setDesc( 'The URL: "' + response.getURL() + '" has a directory indexing problem.' )
                    v.setId( response.id )
                    v.setSeverity(severity.LOW)
                    v.setName( 'Directory indexing' )
                    
                    kb.kb.append( self , 'directory' , v )
                    break
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def _getdirectoryIndexingStrings(self):
        dirIndexStr = []
        ### TODO: verify if I need to add more values here, IIS !!!
        dirIndexStr.append("<title>Index of /") 
        dirIndexStr.append('<a href="\\?C=N;O=D">Name</a>') 
        dirIndexStr.append("Last modified</a>")
        dirIndexStr.append("Parent Directory</a>")
        dirIndexStr.append("Directory Listing for")
        dirIndexStr.append("<TITLE>Folder Listing.")
        dirIndexStr.append("<TITLE>Folder Listing.")
        dirIndexStr.append("- Browsing directory ")
        dirIndexStr.append('">\\[To Parent Directory\\]</a><br><br>') # IIS 6.0
        dirIndexStr.append('<A HREF=".*?">.*?</A><br></pre><hr></body></html>') # IIS 5.0
        return dirIndexStr
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'directoryIndexing', 'directory' ), 'URL' )
            
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
        This plugin greps every response directory indexing problems.
        '''
