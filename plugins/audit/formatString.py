'''
formatString.py

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

from core.controllers.w3afException import w3afException
from core.data.fuzzer.fuzzer import createMutants, createFormatString

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity


class formatString(baseAuditPlugin):
    '''
    Find format string vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def audit(self, freq ):
        '''
        Tests an URL for format string vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'formatString plugin is testing: ' + freq.getURL() )
        
        string_list = self._get_string_list()
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        mutants = createMutants( freq , string_list, oResponse=oResponse )
            
        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'formatString' , 'formatString', mutant.getURL() , mutant.getVar() ):

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
            if self._hasNoBug( 'formatString' , 'formatString' , mutant.getURL() , mutant.getVar() ):
                
                for error in self._get_errors():
                    # Check if the error string is in the response
                    if error in response:
                        # And not in the originally requested (non fuzzed) request
                        if not error not in mutant.getOriginalResponseBody():
                            # vuln, vuln!
                            v = vuln.vuln( mutant )
                            v.setPluginName(self.getName())
                            v.setId( response.id )
                            v.setSeverity(severity.MEDIUM)
                            v.setName( 'Format string vulnerability' )
                            msg = 'A possible (detection is really hard...) format string was found at: '
                            msg += mutant.foundAt()
                            v.setDesc( msg )
                            v.addToHighlight( error )
                            kb.kb.append( self, 'formatString', v )
    
    def _get_errors( self ):
        '''
        @return: A list of error strings.
        '''
        res = []
        msg = '<html><head>\n<title>500 Internal Server Error</title>\n</head><body>\n<h1>'
        msg += 'Internal Server Error</h1>'
        res.append(msg)
        return res
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'formatString', 'formatString' ), 'VAR' )
        
    def _get_string_list( self ):
        '''
        @return: This method returns a list of format strings.
        '''
        strings = []
        lengths = [ 1 , 10 , 25, 50, 100 ]
        for i in lengths:
            strings.append( createFormatString( i ) )
        return strings

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
        return ['grep.error500']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds format string bugs.
        
        Users have to know that detecting a format string vulnerability will be only possible if the server is configured
        to return errors, and the application is developed in cgi-c or some other language that allows the programmer to
        do this kind of mistakes.
        '''
