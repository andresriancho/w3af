'''
pluginConfig.py

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

# for parsing plugin options
from core.controllers.misc.parseOptions import parseXML

# For the isinstance
from core.controllers.basePlugin.basePlugin import basePlugin


class pluginConfig(consoleMenu):
    '''
    This class is a menu for configuring plugin internal options.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, w3af, commands=[] ):
        consoleMenu.__init__(self)
        self._menu = {'help':self._help, 'set':self._set,'view':self._view,'back':self._back}
        self._w3af = w3af
        self._commands = commands
        self._Options = {}
    
    def sh( self, prompt, configurableObject ):
        '''
        Starts the shell's main loop.
        
        @parameter configurableObject: An instance of a configurable object (core.controllers.configurable)
        @parameter prompt: The prompt to use in this section of the shell.
        @return: The prompt
        '''
        self._object = configurableObject
        self._Options = parseXML( self._object.getOptionsXML() )
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
            self.mprint('help','You are here. help [command|parameter] prints more specific help.')
            self.mprint('set' ,'Set a parameter value.')
            self.mprint('view','List all configuration parameters and current values.')
            self.mprint('back', 'Return to previous menu.')         

        else:
            if len( parameters ) == 1:
                if parameters[0] in self._menu.keys():
                    if parameters[0] == 'set':
                        om.out.console( 'Set a parameter value.')
                        om.out.console( 'Sintax: set {parameter} {value}')
                    elif parameters[0] == 'list':
                        om.out.console( 'List all configuration parameters and current values.')
                        om.out.console( 'Sintax: list')
                
                elif parameters[0] in self._Options.keys():
                    # Its a help request for a parameter!
                    help = self._Options[parameters[0]]['help']
                    if help != '':
                        msg = 'Help for parameter ' + parameters[0] + ':'
                        l = len( msg )
                        om.out.console( msg )
                        om.out.console( '=' * l )
                        om.out.console( help )
                    else:
                        om.out.console( 'No help available for "' +  parameters[0] +'".')
        
        return True
    
    def _view( self , parameters):
        '''
        List all configurable parameters of a plugin.
        '''
        if len( self._Options.keys() ):
            self.mprintn( ['Parameter','Value','Description'] )
            self.mprintn( ['=========','=====','==========='] )
            for value in self._Options.keys():
                self.mprintn(  [value,self._Options[value]['default'],self._Options[value]['desc'] ] )
        else:
            self.mprint( 'No configurable parameters.','' )
        return True
    
    def _set( self , parameters):
        '''
        Configure a value.
        '''
        if len( parameters ) < 2:
            om.out.console('Invalid call to set, please see the help:')
            self._help( ['set'] )
        else:
            param = parameters[0]
            value = parameters[1:]
            value = ' '.join( value )
            if param in self._Options.keys():
                self._Options[ param ]['default'] = value
                self._saveOptions()
            else:
                om.out.console( 'Unknown parameter.' )
        return True
    
    def _saveOptions( self ):
        '''
        Saves the self._Options to the corresponding object.
        '''
        ### FIXME: This sends plugin options from output plugins to w3afCore
        ### and plugin options from [audit|grep|disc] plugins to output manager
        ### not really a problem... but it aint nice.
        if isinstance( self._object, basePlugin ):
            self._w3af.setPluginOptions( self._object.getName() , self._object.getType(), self._Options )
            om.out.setPluginOptions( self._object.getName() , self._Options )
        else:
            try:
                self._object.setOptions( self._Options )
            except w3afException, w3:
                om.out.error( str(w3) )
        return False
    
    def _back( self, parameters ):
        '''
        Calls plugin.setOptions(...) and then goes back.
        '''
        self._saveOptions()
        return False
