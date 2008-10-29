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
import core.data.constants.severity as severity

import re

class domXss(baseGrepPlugin):
    '''
    Grep every page for traces of DOM XSS.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)

        #
        # Compile the regular expressions
        #
        self._script_re = re.compile('< *script *>(.*?)</ *script *>', re.IGNORECASE | re.DOTALL )

        # Function regular expressions
        self._function_names_re = [ re.compile(i, re.IGNORECASE) for i in self._get_function_names() ]
        
    def _get_function_names( self ):
        '''
        @return: A list of function names that can be used as an attack
        vector in DOM XSS
        '''
        res = []
        res.append('document.write')
        res.append('document.writeln')
        res.append('document.execCommand')
        res.append('document.open')
        res.append('window.open')
        res.append('eval')
        res.append('window.execScript')

        # Add the function invocation regex that matches:
        # eval( a )
        # eval ( abc )
        # eval( 'def' )
        res = [ i + ' *\((.*?)\)' for i in res ]

        return res
    
    def _get_DOM_user_controlled( self ):
        '''
        @return: A list of user controlled variables that can be used as an attack 
        vector in DOM XSS.
        '''
        res = []
        res.append('document.URL')
        res.append('document.URLUnencoded')
        res.append('document.location')
        res.append('document.referrer')
        res.append('window.location')
        return res
        
    def _testResponse(self, request, response):
        '''
        Plugin entry point, search for the DOM XSS vulns.
        @return: None
        '''
        if response.is_text_or_html():
            
            match = self._script_re.search( response.getBody() )
            if match:
                for script_code in match.groups():
                    
                    for function_re in self._function_names_re:
                        parameters = function_re.search( script_code )
                        
                        if parameters:
                            for user_controlled in self._get_DOM_user_controlled():
                                if user_controlled in parameters.groups()[0]:
                                    v = vuln.vuln()
                                    v.setURL( response.getURL() )
                                    v.setId( response.id )
                                    v.setSeverity(severity.LOW)
                                    v.setName( 'DOM Cross site scripting' )
                                    msg = 'The URL: "' + v.getURL() + '" has a DOM XSS '
                                    msg += 'bug using this DOM object: "'+ user_controlled  + '".'
                                    v.setDesc(msg)
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
        can be found here:
            - http://www.webappsec.org/projects/articles/071105.shtml
        '''
