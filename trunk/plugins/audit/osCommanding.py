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


class osCommanding(baseAuditPlugin):
    '''
    Find OS Commanding vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        #
        #   Some internal variables
        #
        self._special_chars = ['', '&&', '|', ';']
        # The wait time of the unfuzzed request
        self._original_wait_time = 0
        self._file_compiled_regex = []
        
        # The wait time of the first test I'm going to perform
        self._wait_time = 4
        # The wait time of the second test I'm going to perform (this one is just to be sure!)
        self._second_wait_time = 9
        

    def audit(self, freq ):
        '''
        Tests an URL for OS Commanding vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'osCommanding plugin is testing: ' + freq.getURL() )
        
        # We are implementing two different ways of detecting OS Commanding
        # vulnerabilities:
        #       - Time delays
        #       - Writing a known file to the HTML output
        # The basic idea is to be able to detect ANY vulnerability, so we use ALL
        # of the known techniques
        self._with_time_delay(freq)
        
        #   Wait until the echo tests finish. I need to do this because of an odd problem with
        #   Python's "with" statement. It seems that if I use two different with statements and
        #   the same thread lock at the same time, the application locks and stops working.
        self._tm.join(self)
        
        self._with_echo(freq)
    
    def _with_time_delay(self, freq):
        '''
        Tests an URL for OS Commanding vulnerabilities using time delays.
        
        @param freq: A fuzzableRequest
        '''
        # Send the fuzzableRequest without any fuzzing, so we can measure the response 
        # time of this script in order to compare it later
        res = self._sendMutant( freq, analyze=False, grepResult=False )
        self._original_wait_time = res.getWaitTime()
        
        # Prepare the strings to create the mutants
        command_list = self._get_wait_commands()
        only_command_strings = [ v.getCommand() for v in command_list ]
        mutants = createMutants( freq , only_command_strings )
        
        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'osCommanding' , 'osCommanding', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyze_wait}
                self._tm.startFunction( target=self._sendMutant, args=targs , \
                                                    kwds=kwds, ownerObj=self )
                                                    
            self._tm.join( self )

    def _with_echo(self, freq):
        '''
        Tests an URL for OS Commanding vulnerabilities using cat/type to write the 
        content of a known file (i.e. /etc/passwd) to the HTML.
        
        @param freq: A fuzzableRequest
        '''
        original_response = self._sendMutant( freq , analyze=False ).getBody()
        # Prepare the strings to create the mutants
        command_list = self._get_echo_commands()
        only_command_strings = [ v.getCommand() for v in command_list ]
        mutants = createMutants( freq , only_command_strings, oResponse=original_response )

        for mutant in mutants:

            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'osCommanding' , 'osCommanding', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyze_echo}
                self._tm.startFunction( target=self._sendMutant, args=targs , \
                                                    kwds=kwds, ownerObj=self )
                
    def _analyze_echo( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the _with_echo method.
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
            if self._hasNoBug( 'osCommanding' , 'osCommanding' , mutant.getURL() , mutant.getVar() ):
                
                file_patterns = self._get_file_patterns()
                for file_pattern_re in file_patterns:
                    
                    match = file_pattern_re.search( response.getBody() )
                    
                    if match\
                    and not file_pattern_re.search( mutant.getOriginalResponseBody() ):
                        # Search for the correct command and separator
                        sentOs, sentSeparator = self._get_os_separator(mutant)

                        # Create the vuln obj
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setName( 'OS commanding vulnerability' )
                        v.setSeverity(severity.HIGH)
                        v['os'] = sentOs
                        v['separator'] = sentSeparator
                        v.setDesc( 'OS Commanding was found at: ' + mutant.foundAt() )
                        v.setDc( mutant.getDc() )
                        v.setId( response.id )
                        v.setURI( response.getURI() )
                        v.addToHighlight( match.group(0) )
                        kb.kb.append( self, 'osCommanding', v )
                        break
    
    def _get_file_patterns(self):
        '''
        @return: A list of file patterns, that if found in the response, indicate that a command
        was successfully executed.
        '''
        if self._file_compiled_regex:
            # returning the already compiled regular expressions
            return self._file_compiled_regex
        
        else:
            # Compile them for the first time, and return the compiled regular expressions
            
            file_patterns = []
            
            # /etc/passwd
            file_patterns.append("root:x:0:0:")  
            file_patterns.append("daemon:x:1:1:")
            file_patterns.append(":/bin/bash")
            file_patterns.append(":/bin/sh")

            # /etc/passwd in AIX
            file_patterns.append("root:!:x:0:0:")
            file_patterns.append("daemon:!:x:1:1:")
            file_patterns.append(":usr/bin/ksh") 

            # boot.ini
            file_patterns.append("\\[boot loader\\]")
            file_patterns.append("default=multi\\(")
            file_patterns.append("\\[operating systems\\]")
            
            # win.ini
            file_patterns.append("\\[fonts\\]")
            
            self._file_compiled_regex = [re.compile(i, re.IGNORECASE) for i in file_patterns]
            
            return self._file_compiled_regex

    def _get_os_separator(self, mutant):
        '''
        @parameter mutant: The mutant that is being analyzed.
        @return: A tuple with the OS and the command separator
        that was used to generate the mutant.
        '''
        # Retrieve the data I need to create the vuln and the info objects
        command_list = self._get_echo_commands()
        command_list.extend( self._get_wait_commands() )
        
        ### BUGBUG: Are you sure that this works as expected?!?!?!
        for comm in command_list:
            if comm.getCommand() in mutant.getModValue():
                sentOs = comm.getOs()
                sentSeparator = comm.getSeparator()
        return sentOs, sentSeparator

    def _analyze_wait( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the _with_time_delay method.
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
            if self._hasNoBug( 'osCommanding' , 'osCommanding' , mutant.getURL() , mutant.getVar() ):
                
                if response.getWaitTime() > (self._original_wait_time + self._wait_time-2) and \
                response.getWaitTime() < (self._original_wait_time + self._wait_time+2):
                    sentOs, sentSeparator = self._get_os_separator(mutant)
                            
                    # This could be because of an osCommanding vuln, or because of an error that
                    # generates a delay in the response; so I'll resend changing the time and see 
                    # what happens
                    original_wait_param = mutant.getModValue()
                    more_wait_param = original_wait_param.replace( \
                                                                str(self._wait_time), \
                                                                str(self._second_wait_time) )
                    mutant.setModValue( more_wait_param )
                    response = self._sendMutant( mutant, analyze=False )
                    
                    if response.getWaitTime() > (self._original_wait_time + self._second_wait_time-3) and \
                    response.getWaitTime() < (self._original_wait_time + self._second_wait_time+3):
                        # Now I can be sure that I found a vuln, I control the time of the response.
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setName( 'OS commanding vulnerability' )
                        v.setSeverity(severity.HIGH)
                        v['os'] = sentOs
                        v['separator'] = sentSeparator
                        v.setDesc( 'OS Commanding was found at: ' + mutant.foundAt() )
                        v.setDc( mutant.getDc() )
                        v.setId( response.id )
                        v.setURI( response.getURI() )
                        kb.kb.append( self, 'osCommanding', v )

                    else:
                        # The first delay existed... I must report something...
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('Possible OS commanding vulnerability')
                        i.setId( response.id )
                        i.setDc( mutant.getDc() )
                        i.setMethod( mutant.getMethod() )
                        i['os'] = sentOs
                        i['separator'] = sentSeparator
                        msg = 'A possible OS Commanding was found at: ' + mutant.foundAt() 
                        msg += 'Please review manually.'
                        i.setDesc( msg )
                        kb.kb.append( self, 'osCommanding', i )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'osCommanding', 'osCommanding' ), 'VAR' )
    
    def _get_echo_commands(self):
        '''
        @return: This method returns a list of commands to try to execute in order
        to print the content of a known file.
        '''
        commands = []
        for special_char in self._special_chars:
            # Unix
            cmd_string = special_char + "/bin/cat /etc/passwd"
            commands.append( command(cmd_string, 'unix', special_char))
            # Windows
            cmd_string = special_char + "type %SYSTEMROOT%\\win.ini"
            commands.append( command(cmd_string, 'windows', special_char))
        
        # Execution quotes
        commands.append( command("`/bin/cat /etc/passwd`", 'unix', '`'))		
        # FoxPro uses run to run os commands. I found one of this vulns !!
        commands.append( command("run type %SYSTEMROOT%\\win.ini", 'windows', 'run'))
        
        # Now I filter the commands based on the targetOS:
        targetOS = cf.cf.getData('targetOS').lower()
        commands = [ c for c in commands if c.getOs() == targetOS or targetOS == 'unknown']

        return commands
    
    def _get_wait_commands( self ):
        '''
        @return: This method returns a list of commands to try to execute in order
        to introduce a time delay.
        '''
        commands = []
        for special_char in self._special_chars:
            # Windows
            cmd_string = special_char + 'ping -n '+str(self._wait_time -1)+' localhost'
            commands.append( command( cmd_string, 'windows', special_char))
            # Unix
            cmd_string = special_char + 'ping -c '+str(self._wait_time)+' localhost'
            commands.append( command( cmd_string, 'unix', special_char))
            # This is needed for solaris 10
            cmd_string = special_char + '/usr/sbin/ping -s localhost 1000 10 '
            commands.append( command( cmd_string, 'unix', special_char))
        
        # Using execution quotes
        commands.append( command( '`ping -n '+str(self._wait_time -1)+' localhost`', 'windows', '`'))
        commands.append( command( '`ping -c '+str(self._wait_time)+' localhost`', 'unix', '`'))
        
        # FoxPro uses the "run" macro to exec os commands. I found one of this vulns !!
        commands.append( command( 'run ping -n '+str(self._wait_time -1)+' localhost', 'windows', 'run '))
        
        # Now I filter the commands based on the targetOS:
        targetOS = cf.cf.getData('targetOS').lower()
        commands = [ c for c in commands if c.getOs() == targetOS or targetOS == 'unknown']
        
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
        This plugin will find OS commanding vulnerabilities. The detection is performed using two different techniques:
            - Time delays
            - Writing a known file to the HTML output
        
        With time delays, the plugin sends specially crafted requests that, if the vulnerability is present, will delay
        the response for 5 seconds (ping -c 5 localhost). 
        
        When using the second technique, the plugin sends specially crafted requests that, if the vulnerability is present, 
        will print the content of a known file (i.e. /etc/passwd) to the HTML output
        
        This plugin has a rather long list of command separators, like ";" and "`" to try to match all programming languages,
        platforms and installations.
        '''


# I define this here, because it is used by the _get_echo_commands
# and _get_wait_commands methods.
class command:
    '''
    Defines a command that is going to be sent to the remote web app.
    '''
    def __init__( self, comm, os, sep ):
        self._comm = comm
        self._os = os
        self._sep = sep
    
    def getOs( self ):
        '''
        @return: The OS
        '''
        return self._os
        
    def getCommand( self ):
        '''
        @return: The Command to be executed
        '''
        return self._comm
        
    def getSeparator( self ):
        '''
        @return: The separator, could be one of ; && | etc.
        '''
        return self._sep
