'''
domXss.py

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
import re
from core.data.getResponseType import *
import core.data.constants.severity as severity

class domXss(baseGrepPlugin):
    '''
    Grep every page for traces of DOM XSS.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._scriptre = re.compile('< *script *>(.*?)</ *script *>',re.IGNORECASE | re.DOTALL )
        
    def _getFunctionNames( self ):
        res = []
        res.append('document.write')
        res.append('document.writeln')
        res.append('document.execCommand')
        res.append('document.open')
        res.append('window.open')
        res.append('eval')
        res.append('window.execScript')
        return res
    
    def _getDOMUserControlled( self ):
        res = []
        res.append('document.URL')
        res.append('document.URLUnencoded')
        res.append('document.location')
        res.append('document.referrer')
        res.append('window.location')
        return res
        
    def _testResponse(self, request, response):
        
        if response.is_text_or_html():
            
            res = self._scriptre.search( response.getBody() )
            if res:
                for scriptCode in res.groups():
                    
                    for functionName in self._getFunctionNames():
                        parameters = re.search( functionName + ' *\((.*?)\)', scriptCode , re.IGNORECASE )
                        
                        if parameters:
                            for userControlled in self._getDOMUserControlled():
                                if userControlled in parameters.groups()[0]:
                                    v = vuln.vuln()
                                    v.setURL( response.getURL() )
                                    v.setId( response.id )
                                    v.setSeverity(severity.LOW)
                                    v.setName( 'DOM Cross site scripting' )                                    
                                    v.setDesc( 'The URL: "' + v.getURL() + '" has a DOM XSS bug using this DOM object: "'+ userControlled  + '".')
                                    kb.kb.append( self, 'domXss', v )
    
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
        self.printUniq( kb.kb.getData( 'domXss', 'domXss' ), 'URL' )
            
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
        This plugin greps every page for traces of DOM XSS. An interesting paper about DOM XSS
        can be found here : http://www.webappsec.org/projects/articles/071105.shtml .
        '''
