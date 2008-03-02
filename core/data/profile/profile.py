'''
profile.py

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

from core.controllers.w3afException import w3afException
import ConfigParser
from core.controllers.misc.parseOptions import *
from core.controllers.misc.factory import *

class profile:
    '''
    This class represents a profile.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, profile_file_name ):
        # The default optionxform transforms the option to lower case; w3af needs the value as it is
        def optionxform( option ):
            return option
            
        self._config = ConfigParser.ConfigParser()
        # Set the new optionxform function
        self._config.optionxform = optionxform
        
        try:
            self._config.read(profile_file_name)
        except:
            raise w3afException('Unknown format in profile: ' + profile_file_name )
        else:
            if len(self._config.sections()) < 1:
                raise w3afException('Unknown format in profile: ' + profile_file_name )
    
    
    
    def getEnabledPlugins( self, pluginType ):
        '''
        @return: A list of enabled plugins of type pluginType
        '''
        res = []
        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            try:
                type, name = section.split('.')
            except:
                pass
            else:
                if type == pluginType:
                    res.append(name)
        return res
        
    def getPluginOptions( self, pluginName, pluginType ):
        '''
        @return: A dict with the options for a plugin. For example: { 'LICENSE_KEY':'AAAA' }
        '''
        # Get the plugin defaults with their types
        pluginInstance = factory('plugins.' + pluginType + '.' + pluginName )
        optionsXML = pluginInstance.getOptionsXML()
        parsedOptions = parseXML( optionsXML )
        
        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            try:
                type, name = section.split('.')
            except:
                pass
            else:
                if type == pluginType and name == pluginName:
                    for option in self._config.options(section):
                        parsedOptions[option]['default'] = self._config.get(section, option)
        return parsedOptions
        
    def getName( self ):
        '''
        @return: The profile name; as stated in the [profile] section
        '''
        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            # or [profile]
            if section == 'profile':
                for option in self._config.options(section):
                    if option == 'name':
                        return self._config.get(section, option)
        
        # Something went wrong
        return None
        
    def getDesc( self ):
        '''
        @return: The profile description; as stated in the [profile] section
        '''
        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            # or [profile]
            if section == 'profile':
                for option in self._config.options(section):
                    if option == 'description':
                        return self._config.get(section, option)
        
        # Something went wrong
        return None
