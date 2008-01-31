'''
profile.py

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
from core.controllers.w3afException import w3afException
from core.controllers.w3afCore import wCore as w3afCore
from core.controllers.misc.parseOptions import parseXML

class profile:
    '''
    This is the base class that defines how profiles should behave.
    '''
    def __init__( self ):
        self._w3af = w3afCore
        
    def getName( self ):
        raise w3afException('Please implement the getName method.')
        
    def getDesc( self ):
        '''
        @return: A ONE LINE description of the scan profile
        '''
        raise w3afException('Please implement the getDesc method.')
        
    def getLongDesc( self ):
        '''
        @return: A LONG description of the scan profile
        '''
        raise w3afException('Please implement the getLongDesc method.')
        
    def getEnabledPlugins( self , type ):
        '''
        @return: A list of activated $type plugins.
        '''
        raise w3afException('Please implement the getEnabledPlugins method.')
        
    def getPluginOptions( self, pluginName, type ):
        '''
        A profile that doesn't change any plugin options would implement this method like :
            self._setDefaultPluginOptions()
            return self._defaultPluginOptions[type][pluginName]
        '''
        raise w3afException('Please implement the getPluginOptions method.')
    
    def _setDefaultPluginOptions( self ):
        '''
        This method reads the options (as returned by getOptionsXML) of all enabled plugins and saves them to
        the self._defaultPluginOptions attribute. After a call to this method, a profile creator can perform this:
        
            self._defaultPluginOptions['plugin-type']['plugin-name']['option-name']['default'] = 'new value'
            
        In order to change the value of a variable.
        
        @return: None, the attribute is changed.
        '''
        self._defaultPluginOptions = {}
        for pluginType in self._w3af.getPluginTypes():
            self._defaultPluginOptions[pluginType] = {}
            for pluginName in self.getEnabledPlugins( pluginType ):
                configurableObject = self._w3af.getPluginInstance( pluginName, pluginType )
                self._defaultPluginOptions[pluginType][pluginName] = parseXML( configurableObject.getOptionsXML() )
                
