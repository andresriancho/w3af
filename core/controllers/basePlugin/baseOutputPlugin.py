'''
baseOutputPlugin.py

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

import inspect

from core.controllers.basePlugin.basePlugin import basePlugin
from core.controllers.w3afException import w3afException
import core.data.constants.severity as severity


class baseOutputPlugin(basePlugin):
    '''
    This is the base class for data output, all output plugins should inherit from it and implement the following methods :
        1. debug( message, verbose )
        2. information( message, verbose )
        3. error( message, verbose )
        4. vulnerability( message, verbose )

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def getType( self ):
        return 'output'

    def __init__(self):
        basePlugin.__init__( self )
        self.verbosity = 0
        
    def logEnabledPlugins(self,  enabledPluginsDict,  pluginOptionsDict):
        '''
        This method is called from the output managerobject. 
        This method should take an action for the enabled plugins 
        and their configuration.
        
        @parameter enabledPluginsDict: As defined in the w3afCore,
            # A dict with plugin types as keys and a list of plugin names as values
            self._strPlugins = {'audit':[],'grep':[],'bruteforce':[],'discovery':[],\
            'evasion':[], 'mangle':[], 'output':[]}
        
        @parameter pluginOptionsDict: As defined in the w3afCore,
            self._pluginsOptions = {'audit':{},'grep':{},'bruteforce':{},'discovery':{},\
            'evasion':{}, 'mangle':{}, 'output':{}, 'attack':{}}
        '''
        raise w3afException('Plugin is not implementing required method logEnabledPlugins' )
        
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method debug' )

    def information(self, message, newLine = True):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for information messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method information' )

    def error(self, message, newLine = True):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for error messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method error' )

    def vulnerability(self, message , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for vulnerability messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method vulnerability' )

    def console(self, message, newLine = True ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for vulnerability messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method console' )
    
    def logHttp(self, request, response ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action to log HTTP requests and responses.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method logHttp.' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        return []
    
    def _cleanString( self, stringToClean ):
        '''
        @parameter stringToClean: A string that should be cleaned before using it in a message object.
        '''
        for char, replace in [('\0','\\0'),('\t','\\t')]: #('\n','\\n'),('\r','\\r'),
            stringToClean = stringToClean.replace(char,replace)
        return stringToClean

    def getCaller( self, whatStackItem=4 ):
        '''
        What I'm going to do is to:
            - inspect the stack and try to find a reference to a plugin
            - if a plugin is the caller, then i'll return something like audit.xss
            - if no plugin is in the caller stack, i'll return the stack item specified by whatStackItem
        
        Maybe you are asking yourself why whatStackItem == 4, well, this is why:
            I know that getCaller method will be in the stack
            I also know that the method that calls getCaller will be in the stack
            I also know that the om.out.XYZ method will be in the stack
            That's 3... so... number 4 is the one that really called me.
        
        @return: The caller of the om.out.XYZ method; this is used to make output more readable.
        '''
        theStack = inspect.stack()
        
        found = False
        for item in theStack:
            if item[1].startswith('plugins/'):
                found = True
                break
        
        if found:
            # Now I have the caller item from the stack, I want to do some things with it...        
            res = item[1].replace('plugins/','')
            res = res.replace('/','.')
            res = res.replace('.py','')
        else:
            # From the unknown caller, I just need the name of the function
            item = theStack[ whatStackItem ]
            res = item[1].split('/')[-1:][0]
            res = res.replace('.py','')
        
        return res
        
    def getMessageCache(self):
        '''
        Ouput plugins with caches should implement this method.
        Used in the webUI.
        '''
        return {}
