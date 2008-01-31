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
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
import core.data.constants.severity as severity

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
        foundPattern = self._findXpathError( response.getBody() )
        if foundPattern and foundPattern not in mutant.getOriginalResponseBody():
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
    
    def _findXpathError( self, htmlString ):
        '''
        This method searches for xpath errors in html's.
        
        @parameter code: The response code for the test.
        @parameter htmlString: The html string where the method searches for sql errors
        @return: True if a xpath was found on the site, False otherwise.
        '''
        for xpathError in  self._getxpathErrors():
            position = htmlString.lower().find( xpathError )
            if  position != -1:
                om.out.vulnerability('Found xpath injection. The error showed by the web application is (only a fragment is shown): "' + xpathError + '".')
                return xpathError
                
        return False
        
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
        errorStr.append( "Expected ')' in" )
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
        errorStr.append( "Expected token ']'" )
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
        
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
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
