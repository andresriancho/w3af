"""
profiles.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import os

import w3af.core.data.kb.config as cf

from w3af.core.controllers.misc_settings import MiscSettings
from w3af.core.controllers.misc.get_local_ip import get_local_ip
from w3af.core.controllers.misc.get_file_list import get_file_list
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.homeDir import HOME_DIR
from w3af.core.data.profile.profile import profile as profile


class w3af_core_profiles(object):

    def __init__(self, w3af_core):
        self._w3af_core = w3af_core

    def save_current_to_new_profile(self, profile_name, profileDesc=''):
        """
        Saves current config to a newly created profile.

        :param profile_name: The profile to clone
        :param profileDesc: The description of the new profile

        :return: The new profile instance if the profile was successfully saved.
                 Else, raise a BaseFrameworkException.
        """
        # Create the new profile.
        profile_inst = profile()
        profile_inst.set_desc(profileDesc)
        profile_inst.set_name(profile_name)
        profile_inst.save(profile_name)

        # Save current to profile
        return self.save_current_to_profile(profile_name, profileDesc)

    def save_current_to_profile(self, profile_name, prof_desc='', prof_path=''):
        """
        Save the current configuration of the core to the profile called
        profile_name.

        :return: The new profile instance if the profile was successfully saved.
            otherwise raise a BaseFrameworkException.
        """
        # Open the already existing profile
        new_profile = profile(profile_name, workdir=os.path.dirname(prof_path))

        # Save the enabled plugins
        for pType in self._w3af_core.plugins.get_plugin_types():
            enabledPlugins = []
            for pName in self._w3af_core.plugins.get_enabled_plugins(pType):
                enabledPlugins.append(pName)
            new_profile.set_enabled_plugins(pType, enabledPlugins)

        # Save the profile options
        for pType in self._w3af_core.plugins.get_plugin_types():
            for pName in self._w3af_core.plugins.get_enabled_plugins(pType):
                pOptions = self._w3af_core.plugins.get_plugin_options(
                    pType, pName)
                if pOptions:
                    new_profile.set_plugin_options(pType, pName, pOptions)

        # Save the profile targets
        targets = cf.cf.get('targets')
        if targets:
            new_profile.set_target(' , '.join(t.url_string for t in targets))

        # Save the misc and http settings
        misc_settings = MiscSettings()
        new_profile.set_misc_settings(misc_settings.get_options())
        new_profile.set_http_settings(
            self._w3af_core.uri_opener.settings.get_options())

        # Save the profile name and description
        new_profile.set_desc(prof_desc)
        new_profile.set_name(profile_name)

        # Save the profile to the file
        new_profile.save(profile_name)

        return new_profile

    def use_profile(self, profile_name, workdir=None):
        """
        Gets all the information from the profile and stores it in the
        w3af core plugins / target attributes for later use.

        @raise BaseFrameworkException: if the profile to load has some type of problem.
        """
        # Clear all enabled plugins if profile_name is None
        if profile_name is None:
            self._w3af_core.plugins.zero_enabled_plugins()
            return

        # This might raise an exception (which we don't want to handle) when
        # the profile does not exist
        profile_inst = profile(profile_name, workdir)
        
        # It exists, work with it!

        # Set the target settings of the profile to the core
        self._w3af_core.target.set_options(profile_inst.get_target())

        # Set the misc and http settings
        #
        # IGNORE the following parameters from the profile:
        #   - misc_settings.local_ip_address
        #
        profile_misc_settings = profile_inst.get_misc_settings()
        if 'local_ip_address' in profile_inst.get_misc_settings():
            profile_misc_settings['local_ip_address'].set_value(get_local_ip())

        misc_settings = MiscSettings()
        misc_settings.set_options(profile_misc_settings)
        self._w3af_core.uri_opener.settings.set_options(
            profile_inst.get_http_settings())

        #
        #    Handle plugin options
        #
        error_fmt = ('The profile you are trying to load (%s) seems to be'
                     ' outdated, this is a common issue which happens when the'
                     ' framework is updated and one of its plugins adds/removes'
                     ' one of the configuration parameters referenced by a profile'
                     ', or the plugin is removed all together.\n\n'
                     'The profile was loaded but some of your settings might'
                     ' have been lost. This is the list of issues that were found:\n\n'
                     '    - %s\n'
                     '\nWe recommend you review the specific plugin configurations,'
                     ' apply the required changes and save the profile in order'
                     ' to update it and avoid this message. If this warning does not'
                     ' disappear you can manually edit the profile file to fix it.')

        error_messages = []

        for plugin_type in self._w3af_core.plugins.get_plugin_types():
            plugin_names = profile_inst.get_enabled_plugins(plugin_type)

            # Handle errors that might have been triggered from a possibly
            # invalid profile
            try:
                unknown_plugins = self._w3af_core.plugins.set_plugins(plugin_names,
                                                                      plugin_type,
                                                                      raise_on_error=False)
            except KeyError:
                msg = 'The profile references the "%s" plugin type which is'\
                      ' unknown to the w3af framework.'
                error_messages.append(msg % plugin_type)
                continue
                
            for unknown_plugin in unknown_plugins:
                msg = 'The profile references the "%s.%s" plugin which is unknown.'
                error_messages.append(msg % (plugin_type, unknown_plugin))

            # Now we set the plugin options, which can also trigger errors with "outdated"
            # profiles that users could have in their ~/.w3af/ directory.
            for plugin_name in set(plugin_names) - set(unknown_plugins):

                try:
                    plugin_options = profile_inst.get_plugin_options(
                        plugin_type,
                        plugin_name)
                    self._w3af_core.plugins.set_plugin_options(plugin_type,
                                                               plugin_name,
                                                               plugin_options)
                except BaseFrameworkException, w3e:
                    msg = 'Setting the options for plugin "%s.%s" raised an' \
                          ' exception due to unknown or invalid configuration' \
                          ' parameters.'
                    msg += ' ' + str(w3e)
                    error_messages.append(msg % (plugin_type, plugin_name))

        if error_messages:
            msg = error_fmt % (profile_name, '\n    - '.join(error_messages))
            raise BaseFrameworkException(msg)

    def get_profile_list(self, directory=HOME_DIR):
        """
        :param directory: The directory from which profiles are loaded

        :return: Two different lists:
            - One that contains the instances of the valid profiles that were loaded
            - One with the file names of the profiles that are invalid

        >>> HOME_DIR = '.'
        >>> p = w3af_core_profiles(None)
        >>> valid, invalid = p.get_profile_list(HOME_DIR)
        >>> valid_lower = [prof.get_name().lower() for prof in valid]
        >>> 'owasp_top10' in valid_lower
        True

        """
        profile_home = os.path.join(directory, 'profiles')
        str_profile_list = get_file_list(profile_home, extension='.pw3af')

        instance_list = []
        invalid_profiles = []

        for profile_name in str_profile_list:
            profile_filename = os.path.join(
                profile_home, profile_name + '.pw3af')
            try:
                profile_instance = profile(profile_filename)
            except BaseFrameworkException:
                invalid_profiles.append(profile_filename)
            else:
                instance_list.append(profile_instance)
        return instance_list, invalid_profiles

    def remove_profile(self, profile_name):
        """
        :return: True if the profile was successfully removed. Else, raise a BaseFrameworkException.
        """
        profile_inst = profile(profile_name)
        profile_inst.remove()
        return True
