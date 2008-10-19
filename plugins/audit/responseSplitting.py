'''
responseSplitting.py

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

from core.data.fuzzer.fuzzer import createMutants
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

class responseSplitting(baseAuditPlugin):
    '''
    Find response splitting vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for response splitting vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'responseSplitting plugin is testing: ' + freq.getURL() )
        
        rsList = self._getResponseSplitStrings()
        mutants = createMutants( freq , rsList )
            
        for mutant in mutants:
            if self._hasNoBug( 'responseSplitting', 'responseSplitting', mutant.getURL(), mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
            
    def _getErrors( self ):
        '''
        @return: A list of error strings produced by the programming framework when
        we try to modify a header, and the HTML output is already being written to
        the cable, or something similar.
        '''
        res = []
        res.append( 'Header may not contain more than a single header, new line detected' )
        res.append( 'Cannot modify header information - headers already sent' )
        return res
    
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        # When trying to send a response splitting to php 5.1.2 I get :
        # Header may not contain more than a single header, new line detected
        for error in self._getErrors():
            
            # Remember that httpResponse objects have a faster "__in__" than
            # the one in strings; so string in response.getBody() is slower than
            # string in response            
            if error in response:
                msg = 'The variable "' + mutant.getVar() + '" of the URL ' + mutant.getURL()
                msg += ' modifies the headers of the response, but this error was sent while '
                msg += 'testing for response splitting: "' + error + '"'
                
                i = info.info()
                i.setDesc( msg )
                i.setId( response.id )
                i.setName( 'Parameter modifies headers' )
                kb.kb.append( self, 'responseSplitting', i )

                return
            
        if self._checkHeaders( response ):
            v = vuln.vuln( mutant )
            v.setDesc( 'Response Splitting was found at: ' + mutant.foundAt() )
            v.setId( response.id )
            v.setSeverity(severity.MEDIUM)
            v.setName( 'Response splitting vulnerability' )
            kb.kb.append( self, 'responseSplitting', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'responseSplitting', 'responseSplitting' ), 'VAR' )
    
    def _getResponseSplitStrings( self ):
        '''
        With setOptions the user entered a URL that is the one to be included.
        This method returns that URL.
        
        @return: A string, see above.
        '''
        responseSplitStrings = []
        # This will simply add a header saying : "Vulnerable: Yes"  (if vulnerable)
        # \r\n will be encoded to %0d%0a
        responseSplitStrings.append("w3af\r\nVulnerable: Yes")
                
        return responseSplitStrings
        
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
        
    def _checkHeaders( self, response ):
        '''
        This method verifies if a header was successfully injected
        
        @parameter response: The HTTP response where I want to find the injected header.
        @return: True / False
        '''
        headers = response.getHeaders()
        if 'vulnerable' in headers.keys():
            if headers['vulnerable'] == 'Yes':
                return True
            else:
                msg = 'The vulnerable header was added to the HTTP response, '
                msg += 'but the value is not what w3af expected (Vulnerable: Yes)'
                msg += ' Please verify manually.'
                om.out.information(msg)
                
                i = info.info()
                i.setDesc( msg )
                i.setId( response.id )
                i.setName( 'Parameter modifies headers' )
                kb.kb.append( self, 'responseSplitting', i )
                
                return False
        else:
            return False

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
        This plugin will find response splitting vulnerabilities. 
        
        The detection is done by sending "w3af\\r\\nVulnerable: Yes" to every injection point, and reading the
        response headers searching for a header with name "Vulnerable" and value "Yes".
        '''
