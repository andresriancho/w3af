'''
xpath.py

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

import core.data.kb.vuln as vuln
from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
import core.data.constants.severity as severity
import re

class xpath(baseAuditPlugin):
    '''
    Find XPATH injection vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for xpath injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'xpath plugin is testing: ' + freq.getURL() )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        XpathStr = self._getXpathStrings()
        mutants = createMutants( freq , XpathStr, oResponse=oResponse )
            
        for mutant in mutants:
            if self._hasNoBug( 'xpath', 'xpath', mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
        
    def _getXpathStrings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all xpath strings to test.
        '''
        XpathStr = []
        XpathStr.append("d'z\"0")
        XpathStr.append("<!--") # http://www.owasp.org/index.php/Testing_for_XML_Injection
        # Possibly more should be added, but I don't see the need of doing so long
        return XpathStr
    
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        XpathErrorList = self._findXpathError( response )
        for xpathError in XpathErrorList:
            if not re.search( xpathError, mutant.getOriginalResponseBody(), re.IGNORECASE ):
                v = vuln.vuln( mutant )
                v.setName( 'XPATH injection vulnerability' )
                v.setSeverity(severity.MEDIUM)
                v.setDesc( 'XPATH injection was found at: ' + response.getURL() + ' . Using method: ' + v.getMethod() + '. The data sent was: ' + str(mutant.getDc()) )
                v.setId( response.id )
                kb.kb.append( self, 'xpath', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'xpath', 'xpath' ), 'VAR' )
    
    def _findXpathError( self, response ):
        '''
        This method searches for xpath errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for xpathError in  self._getxpathErrors():
            match = re.search( xpathError, response.getBody() , re.IGNORECASE )
            if  match:
                om.out.information('Found xpath injection. The error showed by the web application is (only a fragment is shown): "' + response.getBody()[match.start():match.end()] + '". The error was found on response with id ' + str(response.id) + '.')
                res.append( xpathError )
        return res
        
    def _getxpathErrors( self ):
        errorStr = []
        errorStr.append('Unknown error in XPath' )
        errorStr.append('org.apache.xpath.XPath' )
        errorStr.append('A closing bracket expected in' )
        errorStr.append( 'An operand in Union Expression does not produce a node-set' )
        errorStr.append( 'Cannot convert expression to a number' )
        errorStr.append( 'Document Axis does not allow any context Location Steps' )
        errorStr.append( 'Empty Path Expression' )
        errorStr.append( 'Empty Relative Location Path' )
        errorStr.append( 'Empty Union Expression' )
        errorStr.append( "Expected '\\)' in" )
        errorStr.append( 'Expected node test or name specification after axis operator' )
        errorStr.append( 'Incompatible XPath key' )
        errorStr.append( 'Incorrect Variable Binding' )
        errorStr.append( 'libxml2 library function failed' )
        errorStr.append( 'libxml2' )
        errorStr.append( 'xmlsec library function' )
        errorStr.append( 'xmlsec' )
        errorStr.append( "error '80004005'" )
        errorStr.append( "A document must contain exactly one root element." )
        errorStr.append( '<font face="Arial" size=2>Expression must evaluate to a node-set.' )
        errorStr.append( "Expected token '\\]'" )
        errorStr.append( "<p>msxml4.dll</font>" )
        errorStr.append( "<p>msxml3.dll</font>" )
        
        # Put this here cause i did not know if it was a sql injection
        # This error appears when you put wierd chars in a lotus notes document
        # search ( nsf files ).
        errorStr.append( '4005 Notes error: Query is not understandable' )
        
        # This one will generate some false positives, but i'll leve it here for now
        # until i have a complete list of errors.
        errorStr.append('xpath')
        errorStr = [ e.lower() for e in errorStr ]
        return errorStr
        
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
        This plugin finds XPATH injections.
        
        To find this vulnerabilities the plugin sends the string "d'z'0" to every injection point, and searches the response
        for XPATH errors.
        '''
