'''
plugins.py

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
from core.ui.consoleUi.pluginConfig import pluginConfig
from core.ui.consoleUi.consoleMenu import consoleMenu
from core.controllers.misc.parseOptions import parseXML

class plugins(consoleMenu):
    '''
    This is the plugins configuration menu for the console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, w3af , commands=[] ):
        consoleMenu.__init__(self)
        self._menu = {'help':self._help, 'list':self._list,'back':self._back}
        for i in w3af.getPluginTypes():
            self._menu[ i ] = ''
        self._w3af = w3af
        self._commands = commands
        self._plugins = {}
    
    def sh( self ):
        '''
        Starts the shell's main loop.
        
        @return: The prompt
        '''
        prompt = 'w3af/plugins>>> '
        self._mainloop( prompt )        
        
    def _exec( self, command ):
        '''
        Executes a user input.
        '''
        command, parameters = self._parse( command )
        
        if command in self._w3af.getPluginTypes():
            return self._pluginCfg( command, parameters )
        else:
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
        
                
    def _help( self, parameters ):
        '''
        Prints a help message to the user.
        '''
        if len( parameters ) == 0:
            om.out.console('The following commands are available:')
            self.mprint('help','You are here. help [command] prints more specific help.')
            self.mprint('list','List all available plugins.')
            for p in self._w3af.getPluginTypes():
                self.mprint( p ,'Enable and configure ' + p + ' plugins.')
            self.mprint('back','Return to previous menu.')

        else:
            if len( parameters ) == 1:
                if parameters[0] in self._menu.keys() or parameters[0] in self._w3af.getPluginTypes():
                    if parameters[0] == 'list':
                        om.out.console( 'List all available plugins.')
                        om.out.console( 'Syntax: list {plugin type}')
                        om.out.console( 'Example: list audit')
                    elif parameters[0] in self._w3af.getPluginTypes():
                        om.out.console( 'Enable, investigate and configure '+ parameters[0] +' plugins.' )
                        om.out.console( '' )
                        om.out.console( 'Syntax: '+parameters[0]+' [config plugin1] [plugin1,plugin2 ... pluginN]')
                        om.out.console( 'Example: '+parameters[0] )
                        om.out.console( 'Result: All enabled '+parameters[0] + ' plugins are listed.')
                        om.out.console( '' )
                        om.out.console( 'Example2: '+parameters[0]+ ' plugin1,plugin2')
                        om.out.console( 'Result: plugin1 and plugin2 are configured to run')
                        om.out.console( '' )
                        om.out.console( 'Example3: '+parameters[0]+ ' config plugin1')
                        om.out.console( 'Result: Enters to the plugin configuration menu.' )
                        om.out.console( '' )
                        om.out.console( 'Example4: '+parameters[0]+ ' all,!plugin3')
                        om.out.console( 'Result: All ' + parameters[0] + ' plugins are configured to run except plugin3.' )
                        om.out.console( '' )
                        om.out.console( 'Syntax: '+parameters[0]+' [desc plugin1]')
                        om.out.console( 'Example1: '+parameters[0]+ ' desc plugin1')
                        om.out.console( 'Result: You will get the plugin description.' )
                else:
                    om.out.console('Help not found.')
                    
        
        return True
    
    def _pluginCfg( self , type, parameters):
        '''
        Handles enabling, disabling and configuring plugins.
        '''
        if len( parameters ) == 0 and type in self._w3af.getPluginTypes():
            
            if type in self._plugins.keys():
                om.out.console( 'Enabled ' +type +' plugins:' )
                for plugin in self._plugins[ type ]:
                    om.out.console( plugin )
            elif self._w3af.getEnabledPlugins( type ):
                om.out.console( 'Enabled ' +type +' plugins:' )
                for plugin in self._w3af.getEnabledPlugins( type ):
                    om.out.console( plugin )
            else:
                om.out.console( 'No '+ type +' plugins configured' )
        else:   
            if parameters[0] == 'config':
                if len( parameters ) == 1:
                    om.out.console('Invalid command, please see the help:')
                    self._help([type,])
                else:
                    try:
                        pConf = pluginConfig( self._w3af, self._commands )
                        pluginName = parameters[1]
                        prompt = 'w3af/plugin/' + pluginName + '>>> '
                        try:
                            configurableObject = self._w3af.getPluginInstance( pluginName, type )
                        except w3afException, e:
                            om.out.console('Error: ' + str(e) )
                        else:                       
                            pConf.sh( prompt, configurableObject )
                    except KeyboardInterrupt:
                        om.out.console( '' )
            elif parameters[0] == 'desc':
                if len( parameters ) == 1:
                    om.out.console('Invalid command, please see the help:')
                    self._help([type,])
                else:
                    pluginName = parameters[1]
                    try:
                        plugin = self._w3af.getPluginInstance( pluginName, type )
                    except w3afException, e:
                        om.out.console('Error: ' + str(e) )
                    else:
                        om.out.console( plugin.getLongDesc() )
            else:
                plugins = ''.join(parameters[0:]).split(',')
                plugins = [ p.replace(' ', '') for p in plugins ]
                
                # First of all, a sanity check.
                if 'all' not in plugins:
                    for p in plugins:
                        if p.startswith('!'):
                            raise w3afException('If you wan\'t to use a negation (!) you should enable all plugins. Please read the examples in the help. Example: all,' + p)

                # This avoids duplicates in the list
                plugins = list( set( plugins ) )    # bleh !
                try:
                    self._w3af.setPlugins( plugins, type )
                except w3afException, w3:
                    om.out.error( str(w3) )
                else:
                    self._plugins[ type ] = plugins
        return True

    def _list(self , parameters):
        '''
        Lists all available [audit|grep|discovery|evasion|output] plugins.
        '''
        if len( parameters ) == 0:
            om.out.console( 'To get a list of plugins use :' )
            om.out.console( 'Syntax: list {plugin type}' )
            om.out.console( 'Example: list audit' )
        else:
            type = parameters[0]
            if type not in self._w3af.getPluginTypes():
                om.out.console('Unknown plugin type.')
            else:
                om.out.console('The plugins that are preceeded by a "+" sign have configurable parameters that can be configured using "' + type + ' config plugin_name"')
                list = self._w3af.getPluginList( parameters[0] )
                for plugin in list:
                    pluginInstance = self._w3af.getPluginInstance( plugin, type )
                    try:
                        if len(parseXML( pluginInstance.getOptionsXML() )) > 0:
                            hasConfig = '+'
                        else:
                            hasConfig = ' '
                    except Exception, e:
                        om.out.error('The "' + plugin + '" raised the following exception while calling getOptionsXML():' + str(e) )
                    
                    self.mprint( hasConfig + ' ' + plugin, pluginInstance.getDesc() )
        return True
        
    def _back( self, parameters ):
        # This is done here so output plugin options are applied.
        if 'console' not in self._w3af.getEnabledPlugins('output') and 'output' in self._plugins.keys()\
        and 'all' not in self._plugins['output']:
            self._plugins['output'].append( 'console' )
            self._w3af.setPlugins( self._plugins['output'] , 'output' )
            
        return False
