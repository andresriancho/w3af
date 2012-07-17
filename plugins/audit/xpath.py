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
from __future__ import with_statement

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.data.esmre.multi_in import multi_in


class xpath(baseAuditPlugin):
    '''
    Find XPATH injection vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    XPATH_PATTERNS = (
        'System.Xml.XPath.XPathException:',
        'MS.Internal.Xml.',
        'Unknown error in XPath',
        'org.apache.xpath.XPath',
        'A closing bracket expected in',
        'An operand in Union Expression does not produce a node-set',
        'Cannot convert expression to a number',
        'Document Axis does not allow any context Location Steps',
        'Empty Path Expression',
        'Empty Relative Location Path',
        'Empty Union Expression',
        "Expected ')' in",
        'Expected node test or name specification after axis operator',
        'Incompatible XPath key',
        'Incorrect Variable Binding',
        'libxml2 library function failed',
        'libxml2',
        'xmlsec library function',
        'xmlsec',
        "error '80004005'",
        "A document must contain exactly one root element.",
        '<font face="Arial" size=2>Expression must evaluate to a node-set.',
        "Expected token ']'",
        "<p>msxml4.dll</font>",
        "<p>msxml3.dll</font>",
            
        # Put this here cause i did not know if it was a sql injection
        # This error appears when you put wierd chars in a lotus notes document
        # search ( nsf files ).
        '4005 Notes error: Query is not understandable',
            
        # This one will generate some false positives, but i'll leve it here for now
        # until i have a complete list of errors.
        'xpath'
    )
    _multi_in = multi_in( XPATH_PATTERNS )

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._errors = []

    def audit(self, freq ):
        '''
        Tests an URL for xpath injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        oResponse = self._uri_opener.send_mutant(freq)
        xpath_strings = self._get_xpath_strings()
        mutants = createMutants( freq , xpath_strings, oResponse=oResponse )
            
        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                 mutants,
                                 self._analyze_result)
        
    def _get_xpath_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all xpath strings to test.
        '''
        xpath_strings = []
        xpath_strings.append("d'z\"0")
        
        # http://www.owasp.org/index.php/Testing_for_XML_Injection
        xpath_strings.append("<!--")
        
        return xpath_strings
    
    def _analyze_result( self, mutant, response ):
        '''
        Analyze results of the _send_mutant method.
        '''
        #
        #   I will only report the vulnerability once.
        #
        if self._has_no_bug(mutant):
            
            xpath_error_list = self._find_xpath_error( response )
            for xpath_error in xpath_error_list:
                if xpath_error not in mutant.getOriginalResponseBody():
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.getName())
                    v.setName( 'XPATH injection vulnerability' )
                    v.setSeverity(severity.MEDIUM)
                    v.setDesc( 'XPATH injection was found at: ' + mutant.foundAt() )
                    v.setId( response.id )
                    v.addToHighlight( xpath_error )
                    kb.kb.append( self, 'xpath', v )
                    break
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.getData( 'xpath', 'xpath' ), 'VAR' )
    
    def _find_xpath_error( self, response ):
        '''
        This method searches for xpath errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for xpath_error_match in self._multi_in.query( response.body ):
            msg = 'Found XPATH injection. The error showed by the web application is (only'
            msg +=' a fragment is shown): "' + xpath_error_match
            msg += '". The error was found on response with id ' + str(response.id) + '.'
            om.out.information( msg )
            res.append( xpath_error_match )
        return res
                
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.error500']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds XPATH injections.
        
        To find this vulnerabilities the plugin sends the string "d'z'0" to
        every injection point, and searches the response for XPATH errors.
        '''
