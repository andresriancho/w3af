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

from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

class osCommanding(baseAuditPlugin):
    '''
    Find OS Commanding vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for OS Commanding vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'osCommanding plugin is testing: ' + freq.getURL() )
        
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
        if response.getWaitTime() > 4 and response.getWaitTime() < 6:
            v = vuln.vuln( mutant )
            # Search for the correct command and separator
            for comm in self._getCommandList():
                if comm.getCommand() == mutant.getModValue():
                    v['os'] = comm.getOs()
                    v['separator'] = comm.getSeparator()
            v.setName( 'OS commanding vulnerability' )
            v.setSeverity(severity.HIGH)
            v.setDesc( 'OS Commanding was found at: ' + response.getURL() + ' . Using method: ' + v.getMethod() + '. The data sent was: ' + str(mutant.getDc()) )
            v.setId( response.id )
            kb.kb.append( self, 'osCommanding', v )
    
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
                commands.append( command( specialChar + ' ping -n 5 localhost','windows',specialChar))
            if cf.cf.getData('targetOS') in ['unix', 'unknown']:                
                commands.append( command( specialChar + ' ping -c 6 localhost','unix',specialChar))
        
        if cf.cf.getData('targetOS') in ['windows', 'unknown']:
            commands.append( command( '` ping -n 5 localhost`','windows',specialChar))
        if cf.cf.getData('targetOS') in ['unix', 'unknown']:            
            commands.append( command( '` ping -c 6 localhost`','unix',specialChar))
            
        # FoxPro uses run to run os commands. I found one of this vulns !!
        if cf.cf.getData('targetOS') in ['windows', 'unknown']:
            commands.append( command( 'run ping -n 5 localhost','windows',specialChar))
        
        return commands
        
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
        This plugin will find OS commanding vulnerabilities. The detection is done by sending a command that if successfully executed
        delays the response for 5 seconds (ping -c 5 localhost), and analyzing the response time.  If the server responds in 5 seconds
        or more, then the aplication has an OS commanding vulnerability.
        
        This plugin has a rather long list of command separators, like ";" and "`" to try to match all programming languages, platforms and 
        installations.
        '''
