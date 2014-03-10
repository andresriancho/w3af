"""
profile.py

Copyright 2006 Andres Riancho

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
import codecs
import ConfigParser
import os
import shutil

from w3af.core.controllers.core_helpers.target import w3af_core_target
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.misc.homeDir import get_home_dir
from w3af.core.data.constants.encodings import UTF8
from w3af.core.controllers.exceptions import BaseFrameworkException


class profile(object):
    """
    This class represents a profile.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, profname='', workdir=None):
        """
        Creating a profile instance like p = profile() is done in order to be
        able to create a new profile from scratch and then call
        save(profname).

        When reading a profile, you should use p = profile(profname).
        """
        # The default optionxform transforms the option to lower case;
        # w3af needs the value as it is
        optionxform = lambda opt: opt

        self._config = ConfigParser.ConfigParser()
        # Set the new optionxform function
        self._config.optionxform = optionxform

        if profname:
            # Get profile name's complete path
            profname = self._get_real_profile_path(profname, workdir)
            with codecs.open(profname, "rb", UTF8) as fp:
                try:
                    self._config.readfp(fp)
                except ConfigParser.Error, cpe:
                    msg = 'ConfigParser error in profile: "%s". Exception: "%s"'
                    raise BaseFrameworkException(msg % (profname, str(cpe)))
                except Exception, e:
                    msg = 'Unknown error in profile: "%s". Exception: "%s"'
                    raise BaseFrameworkException(msg % (profname, str(e)))

        # Save the profname variable
        self._profile_file_name = profname

    def _get_real_profile_path(self, profilename, workdir):
        """
        Return the complete path for `profilename`.

        @raise BaseFrameworkException: If no existing profile file is found this
                              exception is raised with the proper desc
                              message.

        >>> p = profile()
        >>> p._get_real_profile_path('OWASP_TOP10', '.')
        './profiles/OWASP_TOP10.pw3af'

        """
        # Alias for os.path. Minor optimization
        ospath = os.path
        pathexists = os.path.exists

        # Add extension if necessary
        if not profilename.endswith('.pw3af'):
            profilename += '.pw3af'

        if pathexists(profilename):
            return profilename

        # Let's try to find it in the workdir directory.
        if workdir is not None:
            tmp_path = ospath.join(workdir, profilename)
            if pathexists(tmp_path):
                return tmp_path

        # Let's try to find it in the "profiles" directory inside workdir
        if workdir is not None:
            tmp_path = ospath.join(workdir, 'profiles', profilename)
            if pathexists(tmp_path):
                return tmp_path

        if not ospath.isabs(profilename):
            tmp_path = ospath.join(get_home_dir(), 'profiles', profilename)
            if pathexists(tmp_path):
                return tmp_path

        raise BaseFrameworkException('The profile "%s" wasn\'t found.' % profilename)

    def get_profile_file(self):
        """
        :return: The path and name of the file that contains the profile definition.
        """
        return self._profile_file_name

    def remove(self):
        """
        Removes the profile file which was used to create this instance.
        """
        try:
            os.unlink(self._profile_file_name)
        except Exception, e:
            msg = 'An exception occurred while removing the profile. Exception:'
            msg += ' "%s".' % e
            raise BaseFrameworkException(msg)
        else:
            return True

    def copy(self, copyProfileName):
        """
        Create a copy of the profile file into copyProfileName. The directory
        of the profile is kept unless specified.
        """
        new_profilePathAndName = copyProfileName

        # Check path
        if os.path.sep not in copyProfileName:
            dir = os.path.dirname(self._profile_file_name)
            new_profilePathAndName = os.path.join(dir, copyProfileName)

        # Check extension
        if not new_profilePathAndName.endswith('.pw3af'):
            new_profilePathAndName += '.pw3af'

        try:
            shutil.copyfile(self._profile_file_name, new_profilePathAndName)
        except Exception, e:
            msg = 'An exception occurred while copying the profile. Exception:'
            msg += ' "%s".' % e
            raise BaseFrameworkException(msg % e)
        else:
            # Now I have to change the data inside the copied profile, to reflect the changes.
            pNew = profile(new_profilePathAndName)
            pNew.set_name(copyProfileName)
            pNew.save(new_profilePathAndName)

            return True

    def set_enabled_plugins(self, plugin_type, plugin_nameList):
        """
        Set the enabled plugins of type plugin_type.

        :param plugin_type: 'audit', 'output', etc.
        :param plugin_nameList: ['xss', 'sqli'] ...
        :return: None
        """
        # First, get the enabled plugins of the current profile
        currentEnabledPlugins = self.get_enabled_plugins(plugin_type)
        for alreadyEnabledPlugin in currentEnabledPlugins:
            if alreadyEnabledPlugin not in plugin_nameList:
                # The plugin was disabled!
                # I should remove the section from the config
                self._config.remove_section(
                    plugin_type + '.' + alreadyEnabledPlugin)

        # Now enable the plugins that the user wants to run
        for plugin in plugin_nameList:
            try:
                self._config.add_section(plugin_type + "." + plugin)
            except ConfigParser.DuplicateSectionError, ds:
                pass

    def get_enabled_plugins(self, plugin_type):
        """
        :return: A list of enabled plugins of type plugin_type
        """
        res = []
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            try:
                type, name = section.split('.')
            except:
                pass
            else:
                if type == plugin_type:
                    res.append(name)
        return res

    def set_plugin_options(self, plugin_type, plugin_name, options):
        """
        Set the plugin options.
        :param plugin_type: 'audit', 'output', etc.
        :param plugin_name: 'xss', 'sqli', etc.
        :param options: an OptionList
        :return: None
        """
        section = plugin_type + "." + plugin_name
        if section not in self._config.sections():
            self._config.add_section(section)

        for option in options:
            self._config.set(
                section, option.get_name(), option.get_value_str())

    def get_plugin_options(self, plugin_type, plugin_name):
        """
        :return: A dict with the options for a plugin. For example: { 'LICENSE_KEY':'AAAA' }
        """
        # Get the plugin defaults with their types
        plugin_instance = factory('w3af.plugins.%s.%s' % (plugin_type, plugin_name))
        options_list = plugin_instance.get_options()

        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            try:
                type, name = section.split('.')
            except:
                pass
            else:
                if type == plugin_type and name == plugin_name:
                    for option in self._config.options(section):
                        try:
                            value = self._config.get(section, option)
                        except KeyError:
                            # We should never get here...
                            msg = 'The option "%s" is unknown for the "%s" plugin.'
                            raise BaseFrameworkException(msg % (option, plugin_name))
                        else:
                            options_list[option].set_value(value)

        return options_list

    def set_misc_settings(self, options):
        """
        Set the misc settings options.
        :param options: an OptionList
        :return: None
        """
        self._set_x_settings('misc-settings', options)

    def set_http_settings(self, options):
        """
        Set the http settings options.
        :param options: an OptionList
        :return: None
        """
        self._set_x_settings('http-settings', options)

    def _set_x_settings(self, section, options):
        """
        Set the section options.

        :param section: The section name
        :param options: an OptionList
        :return: None
        """
        if section not in self._config.sections():
            self._config.add_section(section)

        for option in options:
            self._config.set(
                section, option.get_name(), option.get_value_str())

    def get_misc_settings(self):
        """
        Get the misc settings options.
        :return: The misc settings in an OptionList
        """
        from w3af.core.controllers.misc_settings import MiscSettings
        misc_settings = MiscSettings()
        return self._get_x_settings('misc-settings', misc_settings)

    def get_http_settings(self):
        """
        Get the http settings options.
        :return: The http settings in an OptionList
        """
        import w3af.core.data.url.opener_settings as opener_settings
        url_settings = opener_settings.OpenerSettings()
        return self._get_x_settings('http-settings', url_settings)

    def _get_x_settings(self, section, configurable_instance):
        """
        :return: An OptionList with the options for a configurable object.
        """
        options_list = configurable_instance.get_options()

        try:
            for option in self._config.options(section):
                try:
                    value = self._config.get(section, option)
                except KeyError, k:
                    # We should never get here...
                    msg = 'The option "%s" is unknown for the "%s" section.' % (option, section)
                    raise BaseFrameworkException(msg)
                else:
                    options_list[option].set_value(value)
        except:
            # This is for back compatibility with old profiles
            # that don't have a http-settings nor misc-settings section
            return options_list

        return options_list

    def set_name(self, name):
        """
        Set the name of the profile.
        :param name: The description of the profile
        :return: None
        """
        section = 'profile'
        if section not in self._config.sections():
            self._config.add_section(section)
        self._config.set(section, 'name', name)

    def get_name(self):
        """
        :return: The profile name; as stated in the [profile] section
        """
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            # or [profile]
            if section == 'profile':
                for option in self._config.options(section):
                    if option == 'name':
                        return self._config.get(section, option)

        # Something went wrong
        return None

    def set_target(self, target):
        """
        Set the target of the profile.
        :param target: The target URL of the profile
        :return: None
        """
        section = 'target'
        if section not in self._config.sections():
            self._config.add_section(section)
        self._config.set(section, 'target', target)

    def get_target(self):
        """
        :return: The profile target with the options (target_os, target_framework, etc.)
        """
        # Get the plugin defaults with their types
        target_instance = w3af_core_target()
        options = target_instance.get_options()

        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            # or [profile] or [target]
            if section == 'target':
                for option in self._config.options(section):
                    options[option].set_value(
                        self._config.get(section, option))

        return options

    def set_desc(self, desc):
        """
        Set the description of the profile.
        :param desc: The description of the profile
        :return: None
        """
        section = 'profile'
        if section not in self._config.sections():
            self._config.add_section(section)
        self._config.set(section, 'description', desc)

    def get_desc(self):
        """
        :return: The profile description; as stated in the [profile] section
        """
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            # or [profile]
            if section == 'profile':
                for option in self._config.options(section):
                    if option == 'description':
                        return self._config.get(section, option)

        # Something went wrong
        return None

    def save(self, file_name=''):
        """
        Saves the profile to file_name.

        :return: None
        """
        if not self._profile_file_name:
            if not file_name:
                raise BaseFrameworkException('Error while saving profile, you didn\'t '
                                    'specified the file name.')
            else:  # The user's specified a file_name!
                if not file_name.endswith('.pw3af'):
                    file_name += '.pw3af'

            if os.path.sep not in file_name:
                file_name = os.path.join(
                    get_home_dir(), 'profiles', file_name)
            self._profile_file_name = file_name

        try:
            file_handler = open(self._profile_file_name, 'w')
        except:
            raise BaseFrameworkException(
                'Failed to open profile file: ' + self._profile_file_name)
        else:
            self._config.write(file_handler)
