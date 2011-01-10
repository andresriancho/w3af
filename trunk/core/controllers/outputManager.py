'''
outputManager.py

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
from core.controllers.misc.factory import factory
# severity constants for vuln messages
import core.data.constants.severity as severity

class outputManager:
    '''
    This class manages output. 
    It has a list of output plugins and sends the events to every plugin on that list.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self._outputPluginList = []
        self._outputPlugins = []
        self._pluginsOptions = {}
        self._echo = True

    def _addOutputPlugin(self, OutputPluginName ):
        '''
        Takes a string with the OutputPluginName, creates the object and adds it to the OutputPluginName
        
        @parameter OutputPluginName: The name of the plugin to add to the list.
        @return: No value is returned.
        '''
        if OutputPluginName == 'all':
            fileList = [ f for f in os.listdir('plugins' +os.path.sep +'output'+os.path.sep) ]    
            strReqPlugins = [ os.path.splitext(f)[0] for f in fileList if os.path.splitext(f)[1] == '.py']
            strReqPlugins.remove ( '__init__' )
            
            for pluginName in strReqPlugins:
                plugin = factory( 'plugins.output.' + pluginName )
                
                if pluginName in self._pluginsOptions.keys():
                    plugin.setOptions( self._pluginsOptions[pluginName] )
                
                # Append the plugin to the list
                self._outputPluginList.append( plugin )
        
        else:
                plugin = factory( 'plugins.output.' + OutputPluginName )
                if OutputPluginName in self._pluginsOptions.keys():
                    plugin.setOptions( self._pluginsOptions[OutputPluginName] )

                    # Append the plugin to the list
                self._outputPluginList.append( plugin )
    
    def endOutputPlugins( self ):
        for oPlugin in self._outputPluginList:
            oPlugin.end()
            
    def logEnabledPlugins(self,  enabledPluginsDict,  pluginOptionsDict):
        '''
        This method logs to the output plugins the enabled plugins and their configuration.
        
        @parameter enabledPluginsDict: As defined in the w3afCore,
            # A dict with plugin types as keys and a list of plugin names as values
            self._strPlugins = {'audit':[],'grep':[],'bruteforce':[],'discovery':[],\
            'evasion':[], 'mangle':[], 'output':[]}
        
        @parameter pluginOptionsDict: As defined in the w3afCore,
            self._pluginsOptions = {'audit':{},'grep':{},'bruteforce':{},'discovery':{},\
            'evasion':{}, 'mangle':{}, 'output':{}, 'attack':{}}
        '''
        for oPlugin in self._outputPluginList:
            oPlugin.logEnabledPlugins(enabledPluginsDict, pluginOptionsDict)
    
    def debug(self, message, newLine = True ):
        '''
        Sends a debug message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        if self._echo:
            try:
                message = unicode( message, 'utf-8', errors='replace').encode('utf-8')
            except:
                pass
            else:
                for oPlugin in self._outputPluginList:
                    oPlugin.debug( message, newLine )
    
    def information(self, message, newLine = True ):
        '''
        Sends a informational message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        if self._echo:
            try:
                message = unicode( message, 'utf-8', errors='replace').encode('utf-8')
            except:
                pass
            else:
                for oPlugin in self._outputPluginList:
                    oPlugin.information( message, newLine )
            
    def error(self, message, newLine = True ):
        '''
        Sends an error message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        if self._echo:
            try:
                message = unicode( message, 'utf-8', errors='replace').encode('utf-8')
            except:
                pass
            else:
                for oPlugin in self._outputPluginList:
                    oPlugin.error( message, newLine )

    def logHttp( self, request, response ):
        '''
        Sends the request/response object pair to every output plugin on the list.
        
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        for oPlugin in self._outputPluginList:
            oPlugin.logHttp( request, response )
            
    def vulnerability(self, message, newLine = True, severity=severity.MEDIUM ):
        '''
        Sends a vulnerability message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        if self._echo:
            try:
                message = unicode( message, 'utf-8', errors='replace').encode('utf-8')
            except:
                pass
            else:
                for oPlugin in self._outputPluginList:
                    oPlugin.vulnerability( message, newLine, severity=severity )

    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        if self._echo:
            try:
                message = unicode( message, 'utf-8', errors='replace').encode('utf-8')
            except:
                pass
            else:
                for oPlugin in self._outputPluginList:
                    oPlugin.console( message, newLine )
    
    def echo( self, onOff ):
        '''
        This method is used to enable/disable the output.
        '''
        self._echo = onOff

    def setOutputPlugins( self, outputPlugins ):
        '''
        @parameter outputPlugins: A list with the names of Output Plugins that will be used.
        @return: No value is returned.
        '''     
        self._outputPluginList = []
        self._outputPlugins = outputPlugins
        
        for pluginName in self._outputPlugins:
            out._addOutputPlugin( pluginName )  
        
        out.debug('Exiting setOutputPlugins()' )
    
    def getOutputPlugins(self):
        return self._outputPlugins
    
    def setPluginOptions(self, pluginName, PluginsOptions ):
        '''
        @parameter PluginsOptions: A tuple with a string and a dictionary with the options for a plugin. For example:\
        { console:{'verbosity':7} }
            
        @return: No value is returned.
        '''
        self._pluginsOptions[pluginName] = PluginsOptions
    
    def getMessageCache(self):
        '''
        Used for the webUI.
        @return: returns a list containing messages in plugins caches, only if defined.
        '''
        res = []
        for oPlugin in self._outputPluginList:
            plugCache = oPlugin.getMessageCache()
            res.extend( plugCache )
        return res
        
out = outputManager()
