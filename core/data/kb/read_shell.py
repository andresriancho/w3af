'''
read_shell.py

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

from core.data.kb.vuln import vuln as vuln
from core.data.kb.exploitResult import exploitResult
from core.controllers.intrusionTools.readMethodHelpers import read_os_detection

import core.controllers.outputManager as om

from core.data.kb.shell import shell

from plugins.attack.payloads.decorators.download_decorator import download_debug


class read_shell(shell):
    '''
    This class represents a shell that can only read files from the remote system.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, v):
        shell.__init__(self, v)
                
    def help( self, command ):
        '''
        Handle the help command.
        
        TODO: When is this going to be called?
        '''
        om.out.console('Available commands:')
        om.out.console('    help                            Display this information')
        om.out.console('    lsp                             List payloads')
        om.out.console('    payload <payload>               Execute "payload" and get the result')
        om.out.console('    read <file>                     Read the remote server <file> and echo to this console')
        om.out.console('    download <remote> <local>       Download <remote> file to <local> file system location')
        om.out.console('    exit                            Exit the shell session')
        om.out.console('')
        om.out.console('All the other commands are executed on the remote server.')
        return True

    @download_debug
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

    def generic_user_input( self, command ):
        '''
        This is the method that is called when a user wants to execute something in the shell.
        
        First, I trap the requests for starting the virtual daemon and the w3afAgent, and if this is not the
        case, I forward the request to the specific_user_input method which should be implemented by all shellAttackPlugins.
        '''
        #
        #    Here I get all the common methods like help, payloads, lsp, etc.
        #
        base_klass_result = shell.generic_user_input(self, command)
        if base_klass_result is not None:
            return base_klass_result
        
        # Get the command and the parameters
        parameters = command.split(' ')[1:]
        command = command.split(' ')[0]
        
        #
        #    Read remote files
        #
        if command == 'read' and len(parameters) == 1:
            filename = parameters[0]
            return self.read( filename )

        #
        #    Download remote files
        #
        elif command == 'download' and len(parameters) == 2:
            remote_filename = parameters[0]
            local_filename = parameters[1]
            return self.download(remote_filename, local_filename)

        #
        #    Call the shell subclass method if needed
        #
        elif hasattr( self, 'specific_user_input'):
            # forward to the plugin
            return self.specific_user_input( command )

    def _identifyOs( self ):
        '''
        Identify the remote operating system by reading different files from the OS.
        '''
        self._rOS = read_os_detection( self.read )
        # TODO: Could we determine this by calling some payloads? 
        self._rSystem = ''
        self._rSystemName = 'linux'
        self._rUser = 'file-reader'
        
    def end( self ):
        '''
        Cleanup. In this case, do nothing.
        '''
        om.out.debug( 'Shell cleanup complete.')
            
    def __repr__( self ):
        '''
        @return: A string representation of this shell.
        '''
        if not self._rOS:
            self._identifyOs()

        return '<shell object (rsystem: "'+self._rOS+'")>'
                    
    __str__ = __repr__

    def read(self, filename):
        '''
        To be overriden by subclasses.
        '''
        pass
