'''
osCommanding.py

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

import core.data.parsers.urlParser as urlParser

# kb stuff
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf

class osCommanding(baseAuditPlugin):
    '''
    Find OS Commanding vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # The wait time of the unfuzzed request
        self._originalWaitTime = 0
        
        # The wait time of the first test I'm going to perform
        self._waitTime = 4
        # The wait time of the second test I'm going to perform (this one is just to be sure!)
        self._secondWaitTime = 9
        

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for OS Commanding vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'osCommanding plugin is testing: ' + freq.getURL() )
        
        # Send the fuzzableRequest without any fuzzing, so we can measure the response time of this script
        # in order to compare it later
        self._originalWaitTime = self._sendMutant( freq, analyze=False, grepResult=False ).getWaitTime()
        
        # Prepare the strings to create the mutants
        cList = self._getCommandList()
        onlyCommands = [ v.getCommand() for v in cList ]
        mutants = createMutants( freq , onlyCommands )
        
        for mutant in mutants:
            if self._hasNoBug( 'osCommanding','osCommanding',mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs , ownerObj=self )
        
            
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        if response.getWaitTime() > (self._originalWaitTime + self._waitTime-2) and \
        response.getWaitTime() < (self._originalWaitTime + self._waitTime+2):
            # Retrieve the data I need to create the vuln and the info objects
            for comm in self._getCommandList():
                if comm.getCommand() == mutant.getModValue():
                    sentOs = comm.getOs()
                    sentSeparator = comm.getSeparator()
                    
            # This could be because of an osCommanding vuln, or because of an error that generates a delay
            # in the response; so I'll resend changing the time and see what happens
            moreWaitParam = mutant.getModValue().replace( str(self._waitTime), str(self._secondWaitTime) )
            mutant.setModValue( moreWaitParam )
            response = self._sendMutant( mutant, analyze=False )
            
            if response.getWaitTime() > (self._originalWaitTime + self._secondWaitTime-3) and \
            response.getWaitTime() < (self._originalWaitTime + self._secondWaitTime+3):
                # Now I can be sure that I found a vuln, I control the time of the response.
                v = vuln.vuln( mutant )
                # Search for the correct command and separator
                v.setName( 'OS commanding vulnerability' )
                v.setSeverity(severity.HIGH)
                v['os'] = sentOs
                v['separator'] = sentSeparator
                v.setDesc( 'OS Commanding was found at: ' + response.getURL() + ' . Using method: ' + v.getMethod() + '. The data sent was: ' + str(mutant.getDc()) )
                v.setDc( mutant.getDc() )
                v.setId( response.id )
                v.setURI( response.getURI() )
                kb.kb.append( self, 'osCommanding', v )

            else:
                # The first delay existed... I must report something...
                i = info.info()
                i.setName('Possible OS commanding vulnerability')
                i.setId( response.id )
                i.setDc( mutant.getDc() )
                i.setMethod( mutant.getMethod() )
                i['os'] = sentOs
                i['separator'] = sentSeparator
                i.setDesc( 'A possible OS Commanding was found at: ' + response.getURL() + ' . Using method: ' + mutant.getMethod() + '. The data sent was: ' + str(mutant.getDc()) +' . Please review manually.' )
                kb.kb.append( self, 'osCommanding', i )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'osCommanding', 'osCommanding' ), 'VAR' )
    
    def _getCommandList( self ):
        '''
        @return: This method returns a list of commands to try to execute.
        '''
        class command:
            def __init__( self, comm, os, sep ):
                self._comm = comm
                self._os = os
                self._sep = sep
            
            def getOs( self ): return self._os
            def getCommand( self ): return self._comm
            def getSeparator( self ): return self._sep
            
        commands = []
        for specialChar in ['','&&','|',';']:
            if cf.cf.getData('targetOS') in ['windows', 'unknown']:
                commands.append( command( specialChar + ' ping -n '+str(self._waitTime -1)+' localhost','windows',specialChar))
            if cf.cf.getData('targetOS') in ['unix', 'unknown']:                
                commands.append( command( specialChar + ' ping -c '+str(self._waitTime)+' localhost','unix',specialChar))
        
        if cf.cf.getData('targetOS') in ['windows', 'unknown']:
            commands.append( command( '` ping -n '+str(self._waitTime -1)+' localhost`','windows',specialChar))
        if cf.cf.getData('targetOS') in ['unix', 'unknown']:            
            commands.append( command( '` ping -c '+str(self._waitTime)+' localhost`','unix',specialChar))
            
        # FoxPro uses run to run os commands. I found one of this vulns !!
        if cf.cf.getData('targetOS') in ['windows', 'unknown']:
            commands.append( command( 'run ping -n '+str(self._waitTime -1)+' localhost','windows',specialChar))
        
        return commands
        
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
        This plugin will find OS commanding vulnerabilities. The detection is done by sending a command that if successfully executed
        delays the response for 5 seconds (ping -c 5 localhost), and analyzing the response time.  If the server responds in 5 seconds
        or more, then the aplication has an OS commanding vulnerability.
        
        This plugin has a rather long list of command separators, like ";" and "`" to try to match all programming languages, platforms and 
        installations.
        '''
