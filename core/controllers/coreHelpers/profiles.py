'''
profiles.py

Copyright 2012 Andres Riancho

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

import core.data.kb.config as cf
import core.controllers.miscSettings as miscSettings
import core.controllers.outputManager as om

from core.controllers.misc.get_local_ip import get_local_ip
from core.controllers.misc.get_file_list import get_file_list
from core.controllers.w3afException import w3afException
from core.controllers.misc.homeDir import HOME_DIR
from core.data.profile.profile import profile as profile


class w3af_core_profiles(object):
    
    def __init__(self, w3af_core):
        self._w3af_core = w3af_core
        
    def saveCurrentToNewProfile( self, profile_name, profileDesc='' ):
        '''
        Saves current config to a newly created profile.
        
        @parameter profile_name: The profile to clone
        @parameter profileDesc: The description of the new profile
        
        @return: The new profile instance if the profile was successfully saved. Else, raise a w3afException.
        '''
        # Create the new profile.
        profileInstance = profile()
        profileInstance.setDesc( profileDesc )
        profileInstance.setName( profile_name )
        profileInstance.save( profile_name )
        
        # Save current to profile
        return self.saveCurrentToProfile( profile_name, profileDesc )

    def saveCurrentToProfile(self, profile_name, prof_desc='', prof_path=''):
        '''
        Save the current configuration of the core to the profile called 
        profile_name.
        
        @return: The new profile instance if the profile was successfully saved.
            otherwise raise a w3afException.
        '''
        # Open the already existing profile
        new_profile = profile(profile_name, workdir=os.path.dirname(prof_path))
        
        # Save the enabled plugins
        for pType in self._w3af_core.plugins.getPluginTypes():
            enabledPlugins = []
            for pName in self._w3af_core.plugins.getEnabledPlugins(pType):
                enabledPlugins.append( pName )
            new_profile.setEnabledPlugins(pType, enabledPlugins)
        
        # Save the profile options
        for pType in self._w3af_core.plugins.getPluginTypes():
            for pName in self._w3af_core.plugins.getEnabledPlugins(pType):
                pOptions = self._w3af_core.plugins.getPluginOptions(pType, pName)
                if pOptions:
                    new_profile.setPluginOptions(pType, pName, pOptions)
                
        # Save the profile targets
        targets = cf.cf.getData('targets')
        if targets:
            new_profile.setTarget(' , '.join(t.url_string for t in targets))
                
        # Save the misc and http settings
        misc_settings = miscSettings.miscSettings()
        new_profile.setMiscSettings(misc_settings.getOptions())
        new_profile.setHttpSettings(self._w3af_core.uriOpener.settings.getOptions())
        
        # Save the profile name and description
        new_profile.setDesc(prof_desc)
        new_profile.setName(profile_name)
        
        # Save the profile to the file
        new_profile.save(profile_name)
        
        return new_profile
                
    def useProfile(self, profile_name, workdir=None):
        '''
        Gets all the information from the profile and stores it in the
        w3af core plugins / target attributes for later use.
        
        @raise w3afException: if the profile to load has some type of problem.
        '''
        # Clear all enabled plugins if profile_name is None
        if profile_name is None:
            self._w3af_core.plugins.zero_enabled_plugins()
            return
        
        try:            
            profileInstance = profile(profile_name, workdir) 
        except w3afException:
            # The profile doesn't exist!
            raise
        else:
            # It exists, work with it!
            for pluginType in self._w3af_core.plugins.getPluginTypes():
                pluginNames = profileInstance.getEnabledPlugins( pluginType )
                
                # Handle errors that might have been triggered from a possibly invalid profile
                unknown_plugins = self._w3af_core.plugins.setPlugins( pluginNames, pluginType )
                if unknown_plugins:
                    om.out.error('The profile references the following missing plugins:')
                    for unknown_plugin_name in unknown_plugins:
                        om.out.error('- ' + unknown_plugin_name)
                    
                # Now we set the plugin options, which can also trigger errors with "outdated"
                # profiles that users could have in their ~/.w3af/ directory.
                for pluginName in profileInstance.getEnabledPlugins( pluginType ):
                    pluginOptions = profileInstance.getPluginOptions( pluginType, pluginName )
                    try:
                        # FIXME: Does this work with output plugin options?
                        # What about target, http-settings, etc?
                        self._w3af_core.plugins.setPluginOptions( pluginType, 
                                                                  pluginName,
                                                                  pluginOptions )
                    except Exception, e:
                        # This is because of an invalid plugin, or something like that...
                        # Added as a part of the fix of bug #1937272
                        msg = ('The profile you are trying to load seems to be'
                        ' outdated, one of the enabled plugins has a bug or an'
                        ' plugin option that was valid when you created the '
                        'profile was now removed from the framework. The plugin'
                        ' that triggered this exception is "%s", and the '
                        'original exception is: "%s"' % (pluginName, e))
                        om.out.error(msg)
                    
            # Set the target settings of the profile to the core
            self._w3af_core.target.setOptions( profileInstance.getTarget() )
            
            # Set the misc and http settings
            #
            # IGNORE the following parameters from the profile:
            #   - miscSettings.localAddress
            #
            profile_misc_settings = profileInstance.getMiscSettings()
            if 'localAddress' in profileInstance.getMiscSettings():
                profile_misc_settings['localAddress'].setValue(get_local_ip())
            
            misc_settings = miscSettings.miscSettings()
            misc_settings.setOptions( profile_misc_settings )
            self._w3af_core.uriOpener.settings.setOptions( profileInstance.getHttpSettings() )
            
    def getProfileList( self ):
        '''
        @return: Two different lists:
            - One that contains the instances of the valid profiles that were loaded
            - One with the file names of the profiles that are invalid

        >>> HOME_DIR = '.' 
        >>> p = w3af_core_profiles(None)
        >>> valid, invalid = p.getProfileList()
        >>> valid_lower = [prof.getName().lower() for prof in valid]
        >>> 'owasp_top10' in valid_lower
        True
        
        '''
        profile_home = os.path.join(HOME_DIR, 'profiles')
        str_profile_list = get_file_list(profile_home, extension='.pw3af')
        
        instance_list = []
        invalid_profiles = []
        
        for profile_name in str_profile_list:
            profile_filename = os.path.join(profile_home, profile_name + '.pw3af')
            try:
                profile_instance = profile( profile_filename )
            except:
                invalid_profiles.append( profile_filename )
            else:
                instance_list.append( profile_instance )
        return instance_list, invalid_profiles
    
    def removeProfile( self, profile_name ):
        '''
        @return: True if the profile was successfully removed. Else, raise a w3afException.
        '''
        profileInstance = profile( profile_name )
        profileInstance.remove()
        return True
    