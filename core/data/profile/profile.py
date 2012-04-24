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
import codecs
import ConfigParser
import os
import shutil

from core.controllers.coreHelpers.target import w3af_core_target
from core.controllers.misc.factory import factory
from core.controllers.misc.homeDir import get_home_dir
from core.data.constants.encodings import UTF8
from core.controllers.w3afException import w3afException


class profile:
    '''
    This class represents a profile.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__(self, profname='', workdir=None):
        '''
        Creating a profile instance like p = profile() is done in order to be
        able to create a new profile from scratch and then call
        save(profname).
        
        When reading a profile, you should use p = profile(profname).
        '''
        # The default optionxform transforms the option to lower case;
        # w3af needs the value as it is
        optionxform = lambda opt: opt
            
        self._config = ConfigParser.ConfigParser()
        # Set the new optionxform function
        self._config.optionxform = optionxform
        
        if profname:
            # Get profile name's complete path
            profname = self._get_real_profile_name(profname, workdir)
            with codecs.open(profname, "rb", UTF8) as fp:
                try:
                    self._config.readfp(fp)
                except ConfigParser.Error, cpe:
                    msg = 'ConfigParser error in profile: "%s". Exception: "%s"'
                    raise w3afException( msg % (profname, str(cpe)))
                except Exception, e:
                    msg = 'Unknown error in profile: "%s". Exception: "%s"'
                    raise w3afException( msg % (profname, str(e)))

        
        # Save the profname variable
        self._profile_file_name = profname
    
    def _get_real_profile_name(self, profilename, workdir):
        '''
        Return the complete path for `profilename`.
        
        @raise w3afException: If no existing profile file is found this
            exception is raised with the proper desc message.
        '''
        # Alias for os.path. Minor optimization
        ospath = os.path
        pathexists = os.path.exists
        
        # Add extension if necessary
        if not profilename.endswith('.pw3af'):
            profilename += '.pw3af'
        profname = profilename
        
        # Try to find the file
        found = pathexists(profname)
        
        if not (ospath.isabs(profname) or found):
            profname = ospath.join(get_home_dir(), 'profiles', profilename)
            found = pathexists(profname)
            # Ok, let's try to find it in the passed working directory.
            if not found and workdir:
                profname = ospath.join(workdir, profilename)
                found = pathexists(profname)
                        
        if not found:
            raise w3afException('The profile "%s" wasn\'t found.' % profilename)
        return profname
    

    def get_profile_file(self):
        '''
        @return: The path and name of the file that contains the profile definition.
        '''
        return self._profile_file_name
    
    def remove( self ):
        '''
        Removes the profile file which was used to create this instance.
        '''
        try:
            os.unlink( self._profile_file_name )
        except Exception, e:
            raise w3afException('An exception occurred while removing the profile. Exception: ' + str(e))
        else:
            return True
            
    def copy( self, copyProfileName ):
        '''
        Create a copy of the profile file into copyProfileName. The directory of the profile is kept unless specified.
        '''
        newProfilePathAndName = copyProfileName
        
        # Check path
        if os.path.sep not in copyProfileName:
            dir = os.path.dirname( self._profile_file_name )
            newProfilePathAndName = os.path.join( dir, copyProfileName )
        
        # Check extension
        if not newProfilePathAndName.endswith('.pw3af'):
            newProfilePathAndName += '.pw3af'
        
        try:
            shutil.copyfile( self._profile_file_name, newProfilePathAndName )
        except Exception, e:
            raise w3afException('An exception occurred while copying the profile. Exception: ' + str(e))
        else:
            # Now I have to change the data inside the copied profile, to reflect the changes.
            pNew = profile( newProfilePathAndName )
            pNew.setName( copyProfileName )
            pNew.save( newProfilePathAndName )
            
            return True
    
    def setEnabledPlugins( self, pluginType, pluginNameList ):
        '''
        Set the enabled plugins of type pluginType.
        @parameter pluginType: 'audit', 'output', etc.
        @parameter pluginNameList: ['xss', 'sqli'] ...
        @return: None
        '''
        # First, get the enabled plugins of the current profile
        currentEnabledPlugins = self.getEnabledPlugins( pluginType )
        for alreadyEnabledPlugin in currentEnabledPlugins:
            if alreadyEnabledPlugin not in pluginNameList:
                # The plugin was disabled!
                # I should remove the section from the config
                self._config.remove_section( pluginType+'.'+ alreadyEnabledPlugin)
                
        # Now enable the plugins that the user wants to run
        for plugin in pluginNameList:
            try:
                self._config.add_section(pluginType + "." + plugin )
            except ConfigParser.DuplicateSectionError, ds:
                pass
        
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
    
    def setPluginOptions( self, pluginType, pluginName, options ):
        '''
        Set the plugin options.
        @parameter pluginType: 'audit', 'output', etc.
        @parameter pluginName: 'xss', 'sqli', etc.
        @parameter options: an optionList object
        @return: None
        '''
        section = pluginType + "." + pluginName
        if section not in self._config.sections():
            self._config.add_section( section )
            
        for option in options:
            self._config.set( section, option.getName(), option.getValueStr() )
    
    def getPluginOptions( self, pluginType, pluginName ):
        '''
        @return: A dict with the options for a plugin. For example: { 'LICENSE_KEY':'AAAA' }
        '''
        # Get the plugin defaults with their types
        pluginInstance = factory('plugins.' + pluginType + '.' + pluginName )
        optionsMap = pluginInstance.getOptions()
        
        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            try:
                type, name = section.split('.')
            except:
                pass
            else:
                if type == pluginType and name == pluginName:
                    for option in self._config.options(section):
                        try:
                            value = self._config.get(section, option)
                        except KeyError,k:
                            # We should never get here...
                            msg = 'The option "%s" is unknown for the "%s" plugin.'
                            raise w3afException( msg % (option, pluginName) )
                        else:
                            optionsMap[option].setValue(value)

        return optionsMap
        
    def setMiscSettings( self, options ):
        '''
        Set the misc settings options.
        @parameter options: an optionList object
        @return: None
        '''
        self._set_x_settings('misc-settings', options)

    def setHttpSettings( self, options ):
        '''
        Set the http settings options.
        @parameter options: an optionList object
        @return: None
        '''
        self._set_x_settings('http-settings', options)    
        
    def _set_x_settings( self, section, options ):
        '''
        Set the section options.
        
        @parameter section: The section name
        @parameter options: an optionList object
        @return: None
        '''
        if section not in self._config.sections():
            self._config.add_section( section )
            
        for option in options:
            self._config.set( section, option.getName(), option.getValueStr() )

    def getMiscSettings( self ):
        '''
        Get the misc settings options.
        @return: The misc settings in an optionList object
        '''
        import core.controllers.miscSettings as miscSettings
        misc_settings = miscSettings.miscSettings()
        return self._get_x_settings('misc-settings', misc_settings)

    def getHttpSettings( self ):
        '''
        Get the http settings options.
        @return: The http settings in an optionList object
        '''
        # I just need the xUrllib configuration, but I import all the core
        # because I want to use the singleton
        from core.controllers.w3afCore import wCore
        return self._get_x_settings('http-settings', wCore.uriOpener.settings)
        
    def _get_x_settings( self, section, configurable_instance ):
        '''
        @return: An optionList object with the options for a configurable object.
        '''
        optionsMap = configurable_instance.getOptions()

        try:
            for option in self._config.options(section):
                try:
                    value = self._config.get(section, option)
                except KeyError,k:
                    # We should never get here...
                    raise w3afException('The option "' + option + '" is unknown for the "'+ section + '" section.')
                else:
                    optionsMap[option].setValue(value)
        except:
            # This is for back compatibility with old profiles
            # that don't have a http-settings nor misc-settings section 
            return optionsMap

        return optionsMap

    def setName( self, name ):
        '''
        Set the name of the profile.
        @parameter name: The description of the profile
        @return: None
        '''
        section = 'profile'
        if section not in self._config.sections():
            self._config.add_section( section )
        self._config.set( section, 'name', name )
        
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
    
    def setTarget( self, target ):
        '''
        Set the target of the profile.
        @parameter target: The target URL of the profile
        @return: None
        '''
        section = 'target'
        if section not in self._config.sections():
            self._config.add_section( section )
        self._config.set( section, 'target', target )
        
    def getTarget( self ):
        '''
        @return: The profile target with the options (targetOS, targetFramework, etc.)
        '''
        # Get the plugin defaults with their types
        targetInstance = w3af_core_target()
        options = targetInstance.getOptions()

        for section in self._config.sections():
            # Section is something like audit.xss or discovery.webSpider
            # or [profile] or [target]
            if section == 'target':
                for option in self._config.options(section):
                    options[option].setValue( self._config.get(section, option) )
        
        return options
    
    def setDesc( self, desc ):
        '''
        Set the description of the profile.
        @parameter desc: The description of the profile
        @return: None
        '''
        section = 'profile'
        if section not in self._config.sections():
            self._config.add_section( section )
        self._config.set( section, 'description', desc )
            
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
    
    def save(self, file_name=''):
        '''
        Saves the profile to file_name.
        
        @return: None
        '''
        if not self._profile_file_name:
            if not file_name:
                raise w3afException('Error while saving profile, you didn\'t '
                                    'specified the file name.')
            else: # The user's specified a file_name!
                if not file_name.endswith('.pw3af'):
                    file_name += '.pw3af'
                
            if os.path.sep not in file_name:
                file_name = os.path.join(get_home_dir(), 'profiles', file_name )
            self._profile_file_name = file_name
            
        try:
            file_handler = open( self._profile_file_name, 'w')
        except:
            raise w3afException('Failed to open profile file: ' + self._profile_file_name)
        else:
            self._config.write( file_handler )
