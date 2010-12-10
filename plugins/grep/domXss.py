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
import re

import core.controllers.outputManager as om

from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

class domXss(baseGrepPlugin):
    '''
    Grep every page for traces of DOM XSS.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        # User configured parameters
        self._useSmartGrep = True
        self._useSimpleGrep = False
        # Compile the regular expressions
        self._scriptRe = re.compile('< *script *>(.*?)</ *script *>', re.IGNORECASE | re.DOTALL)
        # Function regular expressions
        self._functionNamesRe = [ re.compile(i, re.IGNORECASE) for i in self._getFunctionNames(True) ]
        
    def _getFunctionNames(self, re=False):
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
        # eval( a ), eval ( abc ), eval( 'def' )
        if re:
            res = [ i + ' *\((.*?)\)' for i in res ]
        return res
    
    def _getDomUserControlled(self):
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
        
    def grep(self, request, response):
        '''
        Plugin entry point, search for the DOM XSS vulns.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        res = []

        if not response.is_text_or_html():
            return

        if self._useSimpleGrep:
            res.extend(self._simpleGrep(response))
        if self._useSmartGrep:
            res.extend(self._smartGrep(response))

        for vulnCode in res:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.addToHighlight(vulnCode)
            v.setURL(response.getURL())
            v.setId(response.id)
            v.setSeverity(severity.LOW)
            v.setName('DOM Cross site scripting (Risky JavaScript Code)')
            msg = 'The URL: "' + v.getURL() + '" has a DOM XSS (Risky JavaScript Code) '
            msg += 'bug using: "'+ vulnCode + '".'
            v.setDesc(msg)
            kb.kb.append(self, 'domXss', v)

    def _simpleGrep(self, response):
        '''
        Search for the DOM XSS vulns using simple grep.
        @parameter response: The HTTP response object
        @return: list of risky code items
        '''
        res = []
        riskyCodes = []
        riskyCodes.extend(self._getDomUserControlled())
        riskyCodes.extend(self._getFunctionNames())
        body = response.getBody()

        for riskyCode in riskyCodes:
            if riskyCode in body:
                res.append(riskyCode)
        return res

    def _smartGrep(self, response):
        '''
        Search for the DOM XSS vulns using smart grep (context regex).
        @parameter response: The HTTP response object
        @return: list of dom xss items
        '''
        res = []
        match = self._scriptRe.search(response.getBody())

        if not match:
            return res

        for scriptCode in match.groups():
            for functionRe in self._functionNamesRe:
                parameters = functionRe.search(scriptCode)
                if parameters:
                    for userControlled in self._getDomUserControlled():
                        if userControlled in parameters.groups()[0]:
                            res.append(userControlled)
        return res

    def setOptions(self, optionsMap):
        self._useSimpleGrep = optionsMap['simpleGrep'].getValue()
        self._useSmartGrep = optionsMap['smartGrep'].getValue()
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Use simple grep mechanism'
        h1 = 'Plugin will simply grep responses for risky JavaScript code'
        o1 = option('simpleGrep', self._useSimpleGrep, d1, 'boolean', help=h1)

        d2 = 'Use smart grep mechanism'
        h2 = 'Plugin will use grep templates depended on context to find risky JavaScript code in responses'
        o2 = option('smartGrep', self._useSmartGrep, d2, 'boolean', help=h2)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq(kb.kb.getData('domXss', 'domXss'), None)
            
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for traces of DOM XSS. 
        
        Two configurable parameters exist:
            - simpleGrep
            - smartGrep
        
        An interesting paper about DOM XSS
        can be found here:
            - http://www.webappsec.org/projects/articles/071105.shtml
        '''
