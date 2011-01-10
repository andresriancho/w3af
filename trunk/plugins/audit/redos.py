'''
redos.py

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

# kb stuff
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf

import re


class redos(baseAuditPlugin):
    '''
    Find ReDoS vulnerabilities.
    
    @author: Sebastien Duquette ( sebastien.duquette@gmail.com )
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Some internal variables
        # The wait time of the unfuzzed request
        self._original_wait_time = 0
        
        # The wait time of the first test I'm going to perform
        self._wait_time = 1
    
    def audit(self, freq ):
        '''
        Tests an URL for ReDoS vulnerabilities using time delays.
        
        @param freq: A fuzzableRequest
        '''
        #
        #   We know for a fact that PHP is not vulnerable to this attack
        #
        #   TODO: Add other frameworks that are not vulnerable!
        #
        for powered_by in kb.kb.getData('serverHeader','poweredByString'):
            if 'php' in powered_by.lower():
                return
        
        om.out.debug( 'redos plugin is testing: ' + freq.getURL() )
    
        # Send the fuzzableRequest without any fuzzing, so we can measure the response 
        # time of this script in order to compare it later
        res = self._sendMutant( freq, analyze=False, grepResult=False )
        self._original_wait_time = res.getWaitTime()
        
        # Prepare the strings to create the mutants
        patterns_list = self._get_wait_patterns(run=1)
        mutants = createMutants( freq , patterns_list )
        
        for mutant in mutants:

            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'redos' , 'redos', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyze_wait}
                self._tm.startFunction( target=self._sendMutant, args=targs , \
                                                    kwds=kwds, ownerObj=self )
                                                    
        self._tm.join( self )

    def _analyze_wait( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the audit method.
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
            if self._hasNoBug( 'preg_replace' , 'preg_replace' , mutant.getURL() , mutant.getVar() ):
                
                if response.getWaitTime() > (self._original_wait_time + self._wait_time) :
                    
                    # This could be because of a ReDoS vuln, an error that generates a delay in the
                    # response or simply a network delay; so I'll resend changing the length and see
                    # what happens.
                    
                    first_wait_time = response.getWaitTime()
                    
                    # Replace the old pattern with the new one:
                    original_wait_param = mutant.getModValue()
                    more_wait_param = original_wait_param.replace( 'X', 'XX' )
                    more_wait_param = more_wait_param.replace( '9', '99' )
                    mutant.setModValue( more_wait_param )
                    
                    # send
                    response = self._sendMutant( mutant, analyze=False )
                    
                    # compare the times
                    if response.getWaitTime() > (first_wait_time * 1.5):
                        # Now I can be sure that I found a vuln, I control the time of the response.
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setName( 'ReDoS vulnerability' )
                        v.setSeverity(severity.MEDIUM)
                        v.setDesc( 'ReDoS was found at: ' + mutant.foundAt() )
                        v.setDc( mutant.getDc() )
                        v.setId( response.id )
                        v.setURI( response.getURI() )
                        kb.kb.append( self, 'redos', v )

                    else:
                        # The first delay existed... I must report something...
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('Possible ReDoS vulnerability')
                        i.setId( response.id )
                        i.setDc( mutant.getDc() )
                        i.setMethod( mutant.getMethod() )
                        msg = 'A possible ReDoS was found at: ' + mutant.foundAt() 
                        msg += ' . Please review manually.'
                        i.setDesc( msg )
                        kb.kb.append( self, 'redos', i )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'redos', 'redos' ), 'VAR' )
    
    def _get_wait_patterns( self, run ):
        '''
        @return: This method returns a list of commands to try to execute in order
        to introduce a time delay.
        '''
        patterns = []
        
        patterns.append('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaX!')
        patterns.append('a@a.aaaaaaaaaaaaaaaaaaaaaaX!')
        patterns.append('1111111111111111111111111111111119!')
        
        return patterns
    
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
        return ['discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds ReDoS (regular expression DoS) vulnerabilities as explained here:
            - http://www.checkmarx.com/NewsDetails.aspx?id=23 
        '''
