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
from core.controllers.misc.commonAttackMethods import commonAttackMethods
from core.data.kb.exploitResult import exploitResult
from core.controllers.w3afException import w3afException
from core.controllers.intrusionTools.execMethodHelpers import *

import plugins.attack.payloads.payload_handler as payload_handler

# python stuff
import time


class shell(vuln, exploitResult, commonAttackMethods):
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
        om.out.console('    start vdaemon                   Start the virtual daemon')
        om.out.console('    start w3afAgent                 Start the w3afAgent service')
        om.out.console('    endInteraction                  Exit the shell session')
        om.out.console('')
        om.out.console('All the other commands are executed on the remote server.')
        return True
        
    def rexec( self, command ):
        '''
        This is the method that is called when a user wants to execute something in the remote operating system.
        First, I trap the requests for starting the virtual daemon and the w3afAgent, and if this isn not the
        case, I forward the request to the _rexec method which should be implemented by all shellAttackPlugins.
        '''
        if command.strip() == 'help':
            self.help( command )
        if command == 'start vdaemon':
            # start a vdaemon!
            # (advanced exploitation)
            from core.controllers.vdaemon.vdFactory import getVirtualDaemon
            try:
                vd = getVirtualDaemon(self._rexec)
            except w3afException, w3:
                return 'Error' + str(w3)
            else:
                vd.setRemoteIP( urlParser.getDomain( self.getURL() )  )
                vd.start2()
                # Let the server start
                time.sleep(0.1)
                return 'Successfully started the virtual daemon.'
        elif command == 'start w3afAgent':
            # start a w3afAgent, to do this, I must transfer the agent client to the
            # remote end and start the w3afServer in this local machine
            # all this work is done by the w3afAgentManager, I just need to called
            # start and thats it.
            from core.controllers.w3afAgent.w3afAgentManager import w3afAgentManager
            try:
                agentManager = w3afAgentManager(self._rexec)
            except w3afException, w3:
                return 'Error' + str(w3)
            else:
                agentManager.run()
                return 'Successfully started the w3afAgent.'
        elif hasattr( self, '_rexec'):
            # forward to the plugin
            return self._rexec( command )
        else:
            raise w3afException('Plugins inhereting from baseShellAttackPlugin should implement the _rexec method.')

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

    def _rexec( self, command ):
        '''
        This method should be implemented by all of the classes that inherit from this one.
        rexec is called when a command is being sent to the remote server.
        This is a NON-interactive shell.

        @parameter command: The command to send ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        raise w3afException('You should implement the _rexec method of classes that inherit from "shell"')
    
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
        self._rOS = osDetectionExec( self.rexec )
        if self._rOS == 'linux':
            self._rUser = self.rexec('whoami').strip()
            self._rSystem = self.rexec('uname -o -r -n -m -s').strip()
            self._rSystemName = self.rexec('uname -n').strip()
        elif self._rOS == 'windows':
            self._rUser = self.rexec('echo %USERDOMAIN%\%USERNAME%').strip()
            self._rSystem = self.rexec('echo %COMPUTERNAME% - %OS% - %PROCESSOR_IDENTIFIER%').strip()
            self._rSystemName = self.rexec('echo %COMPUTERNAME%').strip()
        
    def __repr__( self ):
        if not self._rOS:
            self._identifyOs()
        return '<'+self.getName()+' object (ruser: "'+self.getRemoteUser()+'" | rsystem: "'+self.getRemoteSystem()+'")>'
        
    __str__ = __repr__
