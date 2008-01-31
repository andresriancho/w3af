'''
session.py

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

# Import w3af
import core.controllers.w3afCore
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.consoleMenu import consoleMenu

class session(consoleMenu):
    '''
    This is the session configuration menu for the console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, w3af, commands = [] ):
        consoleMenu.__init__(self)
        self._menu = {'help':self._help, 'resume':self._resume,'save':self._save,'back':self._back}
        self._w3af = w3af
        self._commands = commands
    
    def sh( self ):
        '''
        Starts the shell's main loop.
        
        @return: The prompt
        '''
        prompt = 'w3af/session>>> '
        self._mainloop( prompt )
        
    def _exec( self, command ):
        '''
        Executes a user input.
        '''
        command, parameters = self._parse( command )

        if command in self._menu.keys():
            func = self._menu[command]
            return func(parameters)
        else:
            om.out.console( 'command not found' )
            return True
        
    def _help( self, parameters ):
        '''
        Prints a help message to the user.
        '''
        if len( parameters ) == 0:
            om.out.console('The following commands are available:')
            self.mprint('help','You are here. help [command] prints more specific help.')
            self.mprint('save','Save session info to file.')
            self.mprint('resume','Resume a session from file.')
            self.mprint('back','Return to previous menu.')          

        else:
            if len( parameters ) == 1:
                if parameters[0] in self._menu.keys():
                    if parameters[0] == 'save':
                        om.out.console( 'Save the current session to file.' )
                        om.out.console( 'Sintax: save {filename}' )
                    elif parameters[0] == 'resume':
                        om.out.console( 'Resume a session from file.' )
                        om.out.console( 'Sintax: resume {filename}' )
        
        return True
    
    def _save( self , parameters):
        '''
        Saves the session to a file.
        '''
        if not len( parameters ):
            om.out.console( 'Incorrect call to save, please see the help:' )
            self._help( ['save'] )
        else:       
            try:
                self._w3af.saveSession( parameters[0] )
            except w3afException, w3:
                om.out.error( str(w3) )
        return True
    
    def _resume( self , parameters):
        '''
        Resumes the session file.
        '''
        if not len( parameters ):
            om.out.console( 'Incorrect call to resume, please see the help:' )
            self._help( ['resume'] )
        else:               
            try:
                self._w3af.resumeSession( parameters[0] )
            except w3afException, w3:
                om.out.error( str(w3) )
        return True
        
    def _back( self, parameters ):
        return False
