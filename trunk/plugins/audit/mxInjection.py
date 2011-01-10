'''
mxInjection.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


class mxInjection(baseAuditPlugin):
    '''
    Find MX injection vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        '''
        Plugin added just for completeness... I dont really expect to find one of this bugs
        in my life... but well.... if someone , somewhere in the planet ever finds a bug of using
        this plugin... THEN my job has been done :P
        '''
        baseAuditPlugin.__init__(self)
        
        # Internal variables.
        self._errors = []

    def audit(self, freq ):
        '''
        Tests an URL for mx injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'mxInjection plugin is testing: ' + freq.getURL() )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        mx_injection_strings = self._get_MX_injection_strings()
        mutants = createMutants( freq , mx_injection_strings, oResponse=oResponse )
            
        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'mxInjection' , 'mxInjection', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
                
        self._tm.join( self )
        
            
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        #
        #   Only one thread at the time can enter here. This is because I want to report each
        #   vulnerability only once, and by only adding the "if self._hasNoBug" statement, that
        #   could not be done.
        #
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._hasNoBug( 'mxInjection' , 'mxInjection' , mutant.getURL() , mutant.getVar() ):
                
                mx_error_list = self._find_MX_error( response )
                for mx_error_re, mx_error_string in mx_error_list:
                    if not mx_error_re.search( mutant.getOriginalResponseBody() ):
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setName( 'MX injection vulnerability' )
                        v.setSeverity(severity.MEDIUM)
                        v.setDesc( 'MX injection was found at: ' + mutant.foundAt() )
                        v.setId( response.id )
                        v.addToHighlight( mx_error_string )
                        kb.kb.append( self, 'mxInjection', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'mxInjection', 'mxInjection' ), 'VAR' )
    
    def _get_MX_injection_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all mxInjection strings to test. Example: [ '\"','f00000']
        '''
        mx_injection_strings = []
        mx_injection_strings.append('"')
        mx_injection_strings.append('iDontExist')
        mx_injection_strings.append('')
        return mx_injection_strings

    def _find_MX_error( self, response ):
        '''
        This method searches for mx errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for mx_error_re in self._get_MX_errors():
            match = mx_error_re.search( response.getBody() )
            if match:
                res.append( (mx_error_re, match.group(0)) )
        return res

    def _get_MX_errors(self):
        '''
        @return: A list of MX errors.
        '''
        if len(self._errors) != 0:
            #
            #   This will use a little bit more of memory, but will increase the performance of the
            #   plugin considerably, because the regular expressions are going to be compiled
            #   only once, and then used many times.
            #
            return self._errors
            
        else:
            #
            #   Populate the self._errors list with the compiled versions of the regular expressions.
            #
            errors = []
        
            errors.append( 'Unexpected extra arguments to Select' )
            errors.append( 'Bad or malformed request' )
            errors.append( 'Could not access the following folders' )
            errors.append( 'A000' )
            errors.append( 'A001' )
            errors.append( 'Invalid mailbox name' )
            
            error_msg = 'To check for outside changes to the folder list go to the folders page'
            errors.append( error_msg )
            
            #
            #   Now that I have the regular expressions in the "errors" list, I will compile them
            #   and save that into self._errors.
            #
            for re_string in errors:
                self._errors.append( re.compile(re_string, re.IGNORECASE ) )
                
            return self._errors
        
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
        This plugin will find MX injections. This kind of web application errors are mostly seen in
        webmail software. The tests are simple, for every injectable parameter a string with 
        special meaning in the mail server is sent, and if in the response I find a mail server error,
        a vulnerability was found.
        '''
