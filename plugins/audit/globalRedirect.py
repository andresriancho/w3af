'''
globalRedirect.py

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

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import core.data.parsers.dpCache as dpCache
from core.data.fuzzer.fuzzer import createMutants
from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import re


class globalRedirect(baseAuditPlugin):
    '''
    Find scripts that redirect the browser to any site.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._test_site = 'http://w3af.sourceforge.net/'
        self._scriptre = re.compile('< *script.*?>(.*)< */ *script *>', re.IGNORECASE | re.DOTALL )

    def audit(self, freq ):
        '''
        Tests an URL for global redirect vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'golbalRedirect plugin is testing: ' + freq.getURL() )
        
        mutants = createMutants( freq , [self._test_site, ] )
            
        for mutant in mutants:
            if self._hasNoBug( 'globalRedirect' , 'globalRedirect' , mutant.getURL()\
            , mutant.getVar() ):
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
        
        self._tm.join( self )

    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        if self._find_redirect( response ):
            v = vuln.vuln( mutant )
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'Insecure redirection' )
            v.setSeverity(severity.MEDIUM)
            v.setDesc( 'Global redirect was found at: ' + mutant.foundAt() )
            kb.kb.append( self, 'globalRedirect', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'globalRedirect', 'globalRedirect' ), 'VAR' )
        
    def _find_redirect( self, response ):
        '''
        This method checks if the browser was redirected ( using a 302 code ) 
        or is being told to be redirected by javascript or <meta http-equiv="refresh"
        '''
        if response.getRedirURL().startswith( self._test_site ):
            # The script sent a 302, and w3af followed the redirection
            # so the URL is now the test site
            return True
        else:
            # Test for http-equiv redirects
            try:
                dp = dpCache.dpc.getDocumentParserFor( response )
            except w3afException:
                # Failed to find a suitable parser for the document
                return False
            else:
                for redir in dp.getMetaRedir():
                    if redir.count( self._test_site ):
                        return True
            
            # Test for javascript redirects
            # These are some redirects I found on google :
            # location.href = '../htmljavascript.htm';
            # window.location = "http://www.google.com/"
            # window.location.href="http://www.example.com/";
            # location.replace('http://www.example.com/');
            res = self._scriptre.search( response.getBody() )
            if res:
                for scriptCode in res.groups():
                    splittedCode = scriptCode.split('\n')
                    code = []
                    for i in splittedCode:
                        code.extend( i.split(';') )
                        
                    for line in code:
                        if re.search( '(window\.location|location\.).*' + self._test_site, line ):
                            return True
        
        return False
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
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
        This plugin finds global redirection vulnerabilities. This kind of bugs are used for
        phishing and other identity theft attacks. A common example of a global redirection
        would be a script that takes a "url" parameter and when requesting this page, a HTTP
        302 message with the location header to the value of the url parameter is sent in the
        response.
        
        Global redirection vulnerabilities can be found in javascript, META tags and 302 / 301 
        HTTP return codes.
        '''
