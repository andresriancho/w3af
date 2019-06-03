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
import os
import codecs
import shutil
import string
import ConfigParser

from w3af.core.controllers.core_helpers.target import CoreTarget
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.misc.home_dir import get_home_dir
from w3af.core.data.constants.encodings import UTF8
from w3af.core.controllers.exceptions import BaseFrameworkException


class profile(object):
    """
    This class represents a profile.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    PROFILE_SECTION = 'profile'
    EXTENSION = '.pw3af'

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
            profname = self.get_real_profile_path(profname, workdir)
            with codecs.open(profname, "rb", UTF8) as fp:
                try:
                    self._config.readfp(fp)
                except ConfigParser.Error, cpe:
                    msg = 'ConfigParser error in profile: "%s". Exception: "%s"'
                    raise BaseFrameworkException(msg % (profname, cpe))
                except Exception, e:
                    msg = 'Unknown error in profile: "%s". Exception: "%s"'
                    raise BaseFrameworkException(msg % (profname, e))
                else:
                    if not self.get_name():
                        msg = ('The profile with name "%s" does NOT contain a'
                               ' [profile] section with the "name" attribute.')
                        raise BaseFrameworkException(msg % (profname,))

        # Save the profname variable
        self.profile_file_name = profname

    def get_real_profile_path(self, profile_name, workdir):
        """
        Return the complete path for `profile_name`.

        @raise BaseFrameworkException: If no existing profile file is found this
                              exception is raised with the proper desc
                              message.

        >>> p = profile()
        >>> p.get_real_profile_path('OWASP_TOP10', '.')
        './profiles/OWASP_TOP10.pw3af'
        """
        # Add extension if necessary
        if not profile_name.endswith(self.EXTENSION):
            profile_name += self.EXTENSION

        if os.path.exists(profile_name):
            return profile_name

        # Let's try to find the profile in different paths, using the
        # profile_name as a filename
        for profile_path in self.get_profile_paths(workdir):
            _path = os.path.join(profile_path, profile_name)
            if os.path.exists(_path):
                return _path

        # This is the worse case scenario, where the file name is different from
        # the "name = ..." value which is inside the file
        #
        # https://github.com/andresriancho/w3af/issues/561
        for profile_path in self.get_profile_paths(workdir):
            for profile_file in os.listdir(profile_path):

                if not profile_file.endswith(self.EXTENSION):
                    continue

                profile_path_file = os.path.join(profile_path, profile_file)

                with codecs.open(profile_path_file, "rb", UTF8) as fp:
                    config = ConfigParser.ConfigParser()
                    try:
                        config.readfp(fp)
                    except:
                        # Any errors simply break name detection
                        continue

                    try:
                        name = config.get(self.PROFILE_SECTION, 'name')
                    except:
                        # Any errors simply break name detection
                        continue
                    else:
                        if '%s%s' % (name, self.EXTENSION) == profile_name:
                            return profile_path_file

        msg = 'The profile "%s" wasn\'t found.'
        raise BaseFrameworkException(msg % profile_name)

    @staticmethod
    def is_valid_profile_name(profile_name):
        valid = string.ascii_letters + string.digits + '_-'

        for char in profile_name:
            if char not in valid:
                msg = ('Invalid profile name. Allowed characters are '
                       ' letters, digits, _ and - .')
                raise BaseFrameworkException(msg)

        return True

    def get_profile_paths(self, workdir):
        """
        :param workdir: The working directory
        :yield: The directories where we might find profiles
        """
        if workdir is not None:
            if os.path.exists(workdir):
                yield workdir

            profile_path = os.path.join(workdir, 'profiles')
            if os.path.exists(profile_path):
                yield profile_path

        profile_path = os.path.join(get_home_dir(), 'profiles')
        if os.path.exists(profile_path):
            yield profile_path

    def get_profile_file(self):
        """
        :return: The path and name of the file that contains the profile
                 definition.
        """
        return self.profile_file_name

    def remove(self):
        """
        Removes the profile file which was used to create this instance.
        """
        try:
            os.unlink(self.profile_file_name)
        except Exception, e:
            msg = ('An exception occurred while removing the profile.'
                   ' Exception: "%s".')
            raise BaseFrameworkException(msg % e)
        else:
            return True

    def copy(self, copy_profile_name):
        """
        Create a copy of the profile file into copy_profile_name. The directory
        of the profile is kept unless specified.
        """
        new_profile_path_name = copy_profile_name

        # Check path
        if os.path.sep not in copy_profile_name:
            dir = os.path.dirname(self.profile_file_name)
            new_profile_path_name = os.path.join(dir, copy_profile_name)

        # Check extension
        if not new_profile_path_name.endswith(self.EXTENSION):
            new_profile_path_name += self.EXTENSION

        try:
            shutil.copyfile(self.profile_file_name, new_profile_path_name)
        except Exception, e:
            msg = 'An exception occurred while copying the profile. Exception:'
            msg += ' "%s".' % e
            raise BaseFrameworkException(msg % e)
        else:
            # Now I have to change the data inside the copied profile, to
            # reflect the changes.
            new_profile = profile(new_profile_path_name)
            new_profile.set_name(copy_profile_name)
            new_profile.save(new_profile_path_name)

            return True

    def set_enabled_plugins(self, plugin_type, plugin_names):
        """
        Set the enabled plugins of type plugin_type.

        :param plugin_type: 'audit', 'output', etc.
        :param plugin_names: ['xss', 'sqli'] ...
        :return: None
        """
        # First, get the enabled plugins of the current profile
        current_enabled_plugins = self.get_enabled_plugins(plugin_type)
        for already_enabled_plugin in current_enabled_plugins:
            if already_enabled_plugin not in plugin_names:
                # The plugin was disabled!
                # I should remove the section from the config
                section = '%s.%s' % (plugin_type, already_enabled_plugin)
                self._config.remove_section(section)

        # Now enable the plugins that the user wants to run
        for plugin in plugin_names:
            try:
                self._config.add_section(plugin_type + "." + plugin)
            except ConfigParser.DuplicateSectionError:
                pass

    def get_enabled_plugins(self, plugin_type):
        """
        :return: A list of enabled plugins of type plugin_type
        """
        res = []
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            try:
                _type, name = section.split('.')
            except:
                pass
            else:
                if _type == plugin_type:
                    res.append(name)
        return res

    def set_plugin_options(self, plugin_type, plugin_name, options,
                           self_contained=False):
        """
        Set the plugin options.
        :param plugin_type: 'audit', 'output', etc.
        :param plugin_name: 'xss', 'sqli', etc.
        :param options: an OptionList
        :return: None
        """
        section = '%s.%s' % (plugin_type, plugin_name)
        if section not in self._config.sections():
            self._config.add_section(section)

        for option in options:
            value = option.get_value_for_profile(self_contained=self_contained)

            self._config.set(section,
                             option.get_name(),
                             value)

    def get_plugin_options(self, plugin_type, plugin_name):
        """
        :return: A dict with the options for a plugin. For example:
                { 'LICENSE_KEY':'AAAA' }
        """
        # Get the plugin defaults with their types
        plugin = 'w3af.plugins.%s.%s' % (plugin_type, plugin_name)
        plugin_instance = factory(plugin)
        options_list = plugin_instance.get_options()

        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            try:
                _type, name = section.split('.')
            except:
                pass
            else:
                if _type == plugin_type and name == plugin_name:
                    for option in self._config.options(section):
                        try:
                            value = self._config.get(section, option)
                        except KeyError:
                            # We should never get here...
                            msg = ('The option "%s" is unknown for the'
                                   ' "%s" plugin.')
                            args = (option, plugin_name)
                            raise BaseFrameworkException(msg % args)
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
            self._config.set(section, option.get_name(),
                             option.get_value_for_profile())

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
        configurable_options = configurable_instance.get_options()

        try:
            profile_options = self._config.options(section)
        except ConfigParser.NoSectionError:
            # Some profiles don't have an http-settings or misc-settings
            # section, so we return the defaults as returned by the configurable
            # instance
            return configurable_options

        for option in profile_options:
            try:
                value = self._config.get(section, option)
            except KeyError:
                # We should never get here...
                msg = 'The option "%s" is unknown for the "%s" section.'
                raise BaseFrameworkException(msg % (option, section))
            else:
                configurable_options[option].set_value(value)

        return configurable_options

    def set_name(self, name):
        """
        Set the name of the profile.
        :param name: The description of the profile
        :return: None
        """
        if self.PROFILE_SECTION not in self._config.sections():
            self._config.add_section(self.PROFILE_SECTION)

        self._config.set(self.PROFILE_SECTION, 'name', name)

    def get_name(self):
        """
        :return: The profile name; as stated in the [profile] section
        """
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            # or [profile]
            if section == self.PROFILE_SECTION:
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
        :return: The profile target with the options (target_os,
                 target_framework, etc.)
        """
        # Get the plugin defaults with their types
        target_instance = CoreTarget()
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
        if self.PROFILE_SECTION not in self._config.sections():
            self._config.add_section(self.PROFILE_SECTION)

        self._config.set(self.PROFILE_SECTION, 'description', desc)

    def get_desc(self):
        """
        :return: The profile description; as stated in the [profile] section
        """
        for section in self._config.sections():
            # Section is something like audit.xss or crawl.web_spider
            # or [profile]
            if section == self.PROFILE_SECTION:
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
        if not self.profile_file_name:
            if not file_name:
                raise BaseFrameworkException('Error saving profile, profile'
                                             ' file name is required.')
            else:
                # The user's specified a file_name!
                if not file_name.endswith(self.EXTENSION):
                    file_name += self.EXTENSION

            if os.path.sep not in file_name:
                file_name = os.path.join(get_home_dir(), 'profiles', file_name)

            self.profile_file_name = file_name

        try:
            file_handler = open(self.profile_file_name, 'w')
        except:
            msg = 'Failed to open profile file: "%s"'
            raise BaseFrameworkException(msg % self.profile_file_name)
        else:
            self._config.write(file_handler)
