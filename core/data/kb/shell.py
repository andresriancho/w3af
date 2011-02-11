'''
shell.py

Copyright 2007 Andres Riancho

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
from core.controllers.w3afException import w3afException
from core.controllers.intrusionTools.readMethodHelpers import read_os_detection
import core.data.parsers.urlParser as urlParser

import plugins.attack.payloads.payload_handler as payload_handler
import core.controllers.outputManager as om



class shell(vuln, exploitResult):
    '''
    This class represents the output of an attack plugin that gives a shell to the w3af user.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, v):
        vuln.__init__(self, v)
        exploitResult.__init__(self)
        
        self._rOS = None
        self._rSystem = None
        self._rUser = None
        self._rSystemName = None
        self.id = 0
        
    def getRemoteOs( self ):
        return self._rOS
        
    def getRemoteSystem( self ):
        '''
        @return: dz0@sock3t:~/w3af$ uname -o -r -n -m -s 
        Linux sock3t 2.6.15-27-686 i686 GNU/Linux
        '''
        return self._rSystem
        
    def getRemoteUser( self ):
        return self._rUser
    
    def getRemoteSystemName( self ):
        '''
        @return: dz0@sock3t:~/w3af$ uname -n
        sock3t
        '''
        return self._rSystemName
    
    def setUrlOpener( self, uo ):
        self._urlOpener = uo
        
    def getUrlOpener( self ):
        return self._urlOpener

    def help( self, command ):
        '''
        Handle the help command.
        '''
        om.out.console('Available commands:')
        om.out.console('    help                            Display this information')
        om.out.console('    lsp                             List the available payloads')        
        om.out.console('    exit                            Exit the shell session')
        om.out.console('')
        om.out.console('All the other commands are executed on the remote server.')
        return True

    def generic_user_input( self, command ):
        '''
        This is the method that is called when a user wants to execute something in the shell.
        
        First, I trap the requests for starting the virtual daemon and the w3afAgent, and if this is not the
        case, I forward the request to the specific_user_input method which should be implemented by all shellAttackPlugins.
        '''
        # Get the command and the parameters
        parameters = command.split(' ')[1:]
        command = command.split(' ')[0]
        
        #
        #    Commands that are common to all shells:
        #
        if command.strip() == 'help':
            return self.help( command )
            
        elif command == 'payload':
            #
            #    Run the payload
            #
            payload_name = parameters[0]
            return self._payload( payload_name, parameters[1:] )
        
        elif command == 'lsp':
            #
            #    Based on the syscalls that we have available, list the payloads
            #    that can be run
            #
            return self._print_runnable_payloads()


    def end_interaction(self):
        '''
        When the user executes "exit" in the console, this method is called.
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
    
    def _payload(self, payload_name, parameters):
        '''
        Run a payload by name.
        
        @param payload_name: The name of the payload I want to run.
        @param parameters: The parameters as sent by the user.
        '''
        result_str = ''
        
        if payload_name in payload_handler.runnable_payloads(self):
            om.out.debug( 'The payload can be run. Starting execution.' )
            # TODO: The payloads are actually writing to om.out.console
            # by themselves, so this is useless. In order for the
            # result_str = ... to work, we would need a refactoring
            # what usually gets here, are errors.
            result_str = payload_handler.exec_payload( self, payload_name, parameters)
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
        self._rUser = 'generic'
        self._rSystem = 'generic'
        self._rSystemName = 'generic'
        self._rOS = 'generic'
            
    def __repr__( self ):
        if not self._rOS:
            self._identifyOs()
        return '<'+self.getName()+' object (ruser: "'+self.getRemoteUser()+'" | rsystem: "'+self.getRemoteSystem()+'")>'
        
    __str__ = __repr__
