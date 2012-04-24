'''
w3af_core_plugins.py

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
import os
import sys

import core.data.kb.config as cf
import core.controllers.outputManager as om

from core.controllers.misc.get_file_list import get_file_list
from core.controllers.misc.factory import factory
from core.controllers.w3afException import w3afException


class w3af_core_plugins(object):
    
    def __init__(self, w3af_core):
        self._w3af_core = w3af_core
        
        self.initialized = False
        
    def zero_enabled_plugins(self):
        '''
        Init some internal variables; this method is called when the whole 
        process starts, and when the user loads a new profile.
        '''
        # A dict with plugin types as keys and a list of plugin names as values
        self._plugin_name_list = {'audit': [], 'grep': [], 'bruteforce': [],
                                  'discovery': [], 'evasion': [], 'mangle': [],
                                  'output': [], 'auth': []}

        self._plugins_options = {'audit': {}, 'grep': {}, 'bruteforce': {},
                                'discovery': {}, 'evasion': {}, 'mangle': {},
                                'output': {}, 'attack': {}, 'auth': {}}

        # A dict with plugin types as keys and a list of plugin instances as values
        self.plugins = {'audit':[], 'grep':[], 'bruteforce':[], 'discovery':[],
                        'evasion':[], 'mangle':[], 'output':[], 'auth': []}
        
    
    def init_plugins( self ):
        '''
        The user interfaces should run this method *before* calling start(). 
        If they don't do it, an exception is raised.
        '''
        self.initialized = True
        
        # This is inited before all, to have a full logging support.
        om.out.setOutputPlugins( self._plugin_name_list['output'] )
        
        # Create an instance of each requested plugin and add it to the plugin list
        # Plugins are added taking care of plugin dependencies and configuration

        #
        # Create the plugins that are needed during the initial discovery+bruteforce phase
        #
        for plugin_type in ('discovery', 'bruteforce', 'grep', 'mangle', 'auth'):
            self.plugins[plugin_type] = self.plugin_factory( self._plugin_name_list[plugin_type], 
                                                             plugin_type)
        
        #
        # Some extra init steps for grep and mangle plugins
        #
        self._w3af_core.uriOpener.setGrepPlugins( self.plugins['grep'] )
        self._w3af_core.uriOpener.settings.setManglePlugins( self.plugins['mangle'] )

        #
        # Audit plugins are special, since they don't require to be in memory during discovery+bruteforce
        # so I'll create them here just to check that the configurations are fine and then I don't store
        # them anywhere.
        #
        self.plugin_factory( self._plugin_name_list['audit'] , 'audit')


    def setPluginOptions(self, pluginType, pluginName, pluginOptions):
        '''
        @parameter pluginType: The plugin type, like 'audit' or 'discovery'
        @parameter pluginName: The plugin name, like 'sqli' or 'webSpider'
        @parameter pluginOptions: An optionList object with the option objects for a plugin.
        
        @return: No value is returned.
        '''
        if pluginType.lower() == 'output':
            om.out.setPluginOptions(pluginName, pluginOptions)
            
        # The following lines make sure that the plugin will accept the options
        # that the user is setting to it.
        pI = self.getPluginInstance(pluginName, pluginType)
        try:
            pI.setOptions(pluginOptions)
        except Exception:
            raise
        else:
            # Now that we are sure that these options are valid, lets save them
            # so we can use them later!
            self._plugins_options[pluginType][pluginName] = pluginOptions

    def getPluginOptions(self, pluginType, pluginName):
        '''
        Get the options for a plugin.
        
        IMPORTANT NOTE: This method only returns the options for a plugin
        that was previously configured using setPluginOptions. If you wan't
        to get the default options for a plugin, get a plugin instance and
        perform a plugin.getOptions()
        
        @return: An optionList with the plugin options.
        '''
        return self._plugins_options.get(pluginType, {}).get(pluginName, None)
    
    def getAllPluginOptions(self):
        return self._plugins_options
    
    def getAllEnabledPlugins(self):
        return self._plugin_name_list
    
    def getEnabledPlugins( self, pluginType ):
        return self._plugin_name_list[ pluginType ]
    
    def setPlugins( self, pluginNames, pluginType ):
        '''
        This method sets the plugins that w3afCore is going to use. Before this plugin
        existed w3afCore used setDiscoveryPlugins() / setAuditPlugins() / etc , this wasnt
        really extensible and was replaced with a combination of setPlugins and getPluginTypes.
        This way the user interface isnt bound to changes in the plugin types that are added or
        removed.
        
        @parameter pluginNames: A list with the names of the Plugins that will be run.
        @parameter pluginType: The type of the plugin.
        
        @return: A list of plugins that are unknown to the framework. This is mainly used to have
        some error handling related to old profiles, that might reference deprecated plugins.
        '''
        unknown_plugins = []
        
        # Validate the input...
        pluginNames = list( set( pluginNames ) )    # bleh !
        pList = self.getPluginList(  pluginType  )
        for p in pluginNames:
            if p not in pList and p.replace('!','') not in pList and p != 'all':
                unknown_plugins.append( p )
        
        setMap = {
            'discovery': self._setDiscoveryPlugins,
            'audit': self._setAuditPlugins,
            'grep': self._setGrepPlugins,
            'evasion': self._setEvasionPlugins,
            'output': self._setOutputPlugins,
            'mangle': self._setManglePlugins,
            'bruteforce': self._setBruteforcePlugins,
            'auth': self._setAuthPlugins
            }
        
        func = setMap[pluginType]
        func(pluginNames)
        
        return unknown_plugins
    
    def reloadModifiedPlugin(self,  pluginType,  pluginName):
        '''
        When a plugin is modified using the plugin editor, all instances of it
        inside the core have to be "reloaded" so, if the plugin code was changed,
        the core reflects that change.
        
        @parameter pluginType: The plugin type of the modified plugin ('audit','discovery', etc)
        @parameter pluginName: The plugin name of the modified plugin ('xss', 'sqli', etc)
        '''
        try:
            aModule = sys.modules['plugins.' + pluginType + '.' + pluginName ]
        except KeyError:
            msg = 'Tried to reload a plugin that was never imported! (%s.%s)'
            om.out.debug( msg % (pluginType,pluginName) )
        else:
            reload(aModule)
    
    def getPluginTypesDesc( self, pluginType ):
        '''
        @parameter pluginType: The type of plugin for which we want a description.
        @return: A description of the plugin type passed as parameter
        '''
        try:
            __import__('plugins.' + pluginType )
            aModule = sys.modules['plugins.' + pluginType ]
        except Exception:
            raise w3afException('Unknown plugin type: "'+ pluginType + '".')
        else:
            return aModule.getLongDescription()
        
    def getPluginTypes(self):
        '''
        @return: A list with all plugin types.
        '''
        def rem_from_list(ele, lst):
            try:
                lst.remove(ele)
            except:
                pass
        pluginTypes = [x for x in os.listdir('plugins' + os.path.sep)]
        # Now we filter to show only the directories
        pluginTypes = [d for d in pluginTypes 
                       if os.path.isdir(os.path.join('plugins', d))]
        rem_from_list('attack', pluginTypes)
        rem_from_list('tests', pluginTypes)
        rem_from_list('.svn', pluginTypes)
        return pluginTypes
    
    def getPluginList( self, pluginType ):
        '''
        @return: A string list of the names of all available plugins by type.
        '''
        strPluginList = get_file_list( 'plugins' + os.path.sep + pluginType + os.path.sep )
        return strPluginList
        
        
    def getPluginInstance(self, pluginName, pluginType):
        '''
        @return: An instance of a plugin.
        '''
        pluginInst = factory('plugins.' + pluginType + '.' + pluginName)
        pluginInst.setUrlOpener(self._w3af_core.uriOpener)
        if pluginName in self._plugins_options[ pluginType ].keys():
            pluginInst.setOptions(self._plugins_options[pluginType ][pluginName])
        
        # This will init some plugins like mangle and output
        if pluginType == 'attack' and not self.initialized:
            self.init_plugins()
        return pluginInst
    
    def plugin_factory( self, strReqPlugins, pluginType ):
        '''
        This method creates the requested modules list.
        
        @parameter strReqPlugins: A string list with the requested plugins to be executed.
        @parameter pluginType: [audit|discovery|grep]
        @return: A list with plugins to be executed, this list is ordered using the exec priority.
        '''     
        requestedPluginsList = []
        
        if 'all' in strReqPlugins:
            fileList = [ f for f in os.listdir('plugins' + os.path.sep+ pluginType + os.path.sep ) ]    
            allPlugins = [ os.path.splitext(f)[0] for f in fileList if os.path.splitext(f)[1] == '.py' ]
            allPlugins.remove ( '__init__' )
            
            if len ( strReqPlugins ) != 1:
                # [ 'all', '!sqli' ]
                # I want to run all plugins except sqli
                unwantedPlugins = [ x[1:] for x in strReqPlugins if x[0] =='!' ]
                strReqPlugins = list( set(allPlugins) - set(unwantedPlugins) ) #bleh! v2
            else:
                strReqPlugins = allPlugins
            
            # Update the plugin list
            # This update is usefull for cases where the user selected "all" plugins,
            # the self._plugin_name_list[pluginType] is useless if it says 'all'.
            self._plugin_name_list[pluginType] = strReqPlugins
                
        for pluginName in strReqPlugins:
            plugin = factory( 'plugins.' + pluginType + '.' + pluginName )

            # Now we are going to check if the plugin dependencies are met
            for dep in plugin.getPluginDeps():
                try:
                    depType, depPlugin = dep.split('.')
                except:
                    msg = ('Plugin dependencies must be indicated using '
                    'pluginType.pluginName notation. This is an error in '
                    '%s.getPluginDeps().' % pluginName)
                    raise w3afException(msg)
                if depType == pluginType:
                    if depPlugin not in strReqPlugins:
                        if cf.cf.getData('autoDependencies'):
                            strReqPlugins.append( depPlugin )
                            om.out.information('Auto-enabling plugin: ' + pluginType + '.' + depPlugin)
                            # nice recursive call, this solves the "dependency of dependency" problem =)
                            return self.plugin_factory( strReqPlugins, depType )
                        else:
                            msg = ('Plugin "%s" depends on plugin "%s" and '
                            '"%s" is not enabled.' % (pluginName, dep, dep))
                            raise w3afException(msg)
                else:
                    if depPlugin not in self._plugin_name_list[depType]:
                        if cf.cf.getData('autoDependencies'):
                            dependObj = factory( 'plugins.' + depType + '.' + depPlugin )
                            dependObj.setUrlOpener( self._w3af_core.uriOpener )
                            if dependObj not in self.plugins[depType]:
                                self.plugins[depType].insert( 0, dependObj )
                                self._plugin_name_list[depType].append( depPlugin )
                            om.out.information('Auto-enabling plugin: ' + depType + '.' + depPlugin)
                        else:
                            msg = ('Plugin "%s" depends on plugin "%s" and '
                            '"%s" is not enabled.' % (pluginName, dep, dep))
                            raise w3afException(msg)
                    else:
                        # if someone in another planet depends on me... run first
                        self._plugin_name_list[depType].remove( depPlugin )
                        self._plugin_name_list[depType].insert( 0, depPlugin )
            
            # Now we set the plugin options
            if pluginName in self._plugins_options[ pluginType ]:
                pOptions = self._plugins_options[ pluginType ][ pluginName ]
                plugin.setOptions( pOptions )
                
            # This sets the url opener for each module that is called inside the for loop
            plugin.setUrlOpener( self._w3af_core.uriOpener )
            # Append the plugin to the list
            requestedPluginsList.append ( plugin )

        # The plugins are all on the requestedPluginsList, now I need to order them
        # based on the module dependencies. For example, if A depends on B , then
        # B must be run first.
        
        orderedPluginList = []
        for plugin in requestedPluginsList:
            deps = plugin.getPluginDeps()
            if len( deps ) != 0:
                # This plugin has dependencies, I should add the plugins in order
                for plugin2 in requestedPluginsList:
                    if pluginType+'.'+plugin2.getName() in deps and plugin2 not in orderedPluginList:
                        orderedPluginList.insert( 1, plugin2)

            # Check if I was added because of a dep, if I wasnt, add me.
            if plugin not in orderedPluginList:
                orderedPluginList.insert( 100, plugin )
        
        # This should never happend.
        if len(orderedPluginList) != len(requestedPluginsList):
            error_msg = ('There is an error in the way w3afCore orders '
            'plugins. The ordered plugin list length is not equal to the '
            'requested plugin list.')
            om.out.error( error_msg, newLine=False)
            
            om.out.error('The error was found sorting plugins of type: '+ pluginType +'.')
            
            error_msg = ('Please report this bug to the developers including a '
            'complete list of commands that you run to get to this error.')
            om.out.error(error_msg)

            om.out.error('Ordered plugins:')
            for plugin in orderedPluginList:
                om.out.error('- ' + plugin.getName() )

            om.out.error('\nRequested plugins:')
            for plugin in requestedPluginsList:
                om.out.error('- ' + plugin.getName() )

            sys.exit(-1)

        return orderedPluginList
    
    def _setBruteforcePlugins( self, bruteforcePlugins ):
        '''
        @parameter manglePlugins: A list with the names of output Plugins that will be run.
        @return: No value is returned.
        '''
        self._plugin_name_list['bruteforce'] = bruteforcePlugins
    
    def _setManglePlugins( self, manglePlugins ):
        '''
        @parameter manglePlugins: A list with the names of output Plugins that will be run.
        @return: No value is returned.
        '''
        self._plugin_name_list['mangle'] = manglePlugins
    
    def _setOutputPlugins( self, outputPlugins ):
        '''
        @parameter outputPlugins: A list with the names of output Plugins that will be run.
        @return: No value is returned.
        '''
        self._plugin_name_list['output'] = outputPlugins
        
    def _setDiscoveryPlugins( self, discoveryPlugins ):
        '''
        @parameter discoveryPlugins: A list with the names of Discovery Plugins that will be run.
        @return: No value is returned.
        '''         
        self._plugin_name_list['discovery'] = discoveryPlugins
    
    def _setAuditPlugins( self, auditPlugins ):
        '''
        @parameter auditPlugins: A list with the names of Audit Plugins that will be run.
        @return: No value is returned.
        '''         
        self._plugin_name_list['audit'] = auditPlugins
        
    def _setGrepPlugins( self, grepPlugins):
        '''
        @parameter grepPlugins: A list with the names of Grep Plugins that will be used.
        @return: No value is returned.
        '''     
        self._plugin_name_list['grep'] = grepPlugins
        
    def _setEvasionPlugins( self, evasionPlugins ):
        '''
        @parameter evasionPlugins: A list with the names of Evasion Plugins that will be used.
        @return: No value is returned.
        '''
        self._plugin_name_list['evasion'] = evasionPlugins
        self.plugins['evasion'] = self.plugin_factory( evasionPlugins , 'evasion')
        self._w3af_core.uriOpener.setEvasionPlugins( self.plugins['evasion'] )
        
    def _setAuthPlugins( self, authPlugins ):
        '''
        @parameter authlugins: A list with the names of Auth Plugins that will be used.
        @return: No value is returned.
        '''
        self._plugin_name_list['auth'] = authPlugins
