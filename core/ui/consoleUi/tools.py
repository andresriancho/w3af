'''
tools.py

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

# Some traditional imports
import os

# Import w3af
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.consoleMenu import consoleMenu

class tools(consoleMenu):
    '''
    This is the tools menu. Its main objective is to run the tools, its indepentent of w3afCore.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, commands=[] ):
        consoleMenu.__init__(self)
        self._menu = {'help':self._help, 'list':self._list,'back':self._back,'run':self._run}
        self._commands = commands
    
    def sh( self ):
        '''
        Starts the shell's main loop.
        
        @return: The prompt
        '''
        prompt = 'w3af/tools>>> '
        self._mainloop( prompt )
        
    def _exec( self, command ):
        '''
        Executes a user input.
        '''
        command, parameters = self._parse( command )

        if command in self._menu.keys():
            func = self._menu[command]
            try:
                res = func(parameters)
            except w3afException,e:
                om.out.console( str(e) )
            else:
                return res
        else:
            om.out.console( 'command not found' )
            return True
        
    def _parse( self, command ):
        '''
        Parses the user input.
        
        @return: A command and its parameters in a tuple.
        '''
        self._commandHistory.append( command )
        c = command.split(' ')[0]
        p = []
        p.extend( command.split(' ')[1:] )
        return c, p
    
    def _help( self, parameters ):
        '''
        Prints a help message to the user.
        '''
        if len( parameters ) == 0:
            om.out.console('The following commands are available:')
            self.mprint('help','You are here. help [command] prints more specific help.')
            self.mprint('list','List all available tools.')
            self.mprint('run <toolName>','Run toolName and print its output.')
            self.mprint('back','Return to previous menu.')
        else:
            if len( parameters ) == 1:
                if parameters[0] == 'run':
                    self.mprint('Run a tool and print its output.','')
                    self.mprint('Sintaxis: run <toolName>','')
                    self.mprint('Example: run gencc','')
                else:
                    om.out.console('Help not found.')
        
        return True
    
    def _run( self, parameters ):
        '''
        Run an external tool.
        '''
        if len( parameters ) == 0:
            self._help(['run'])
        else:
            if not parameters[0].count('..'):
                os.system( 'python tools' + os.path.sep + parameters[0] + ' '+' '.join( parameters[1:] ) )
            else:
                om.out.information('w3af has no path trasversal bugs ;)')
            return True
        
    def _list(self , parameters):
        '''
        Lists all available [audit|grep|discovery|evasion|output] tools.
        '''
        fileList = [ f for f in os.listdir('tools' + os.path.sep) ]
        if '.svn' in fileList:
            fileList.remove('.svn')
        for file in fileList:
            om.out.console( file )
        return True
        
    def _back( self, parameters ):
        return False
