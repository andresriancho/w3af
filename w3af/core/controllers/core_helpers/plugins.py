"""
plugins.py

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
import sys

from functools import partial

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.misc.get_file_list import get_file_list
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af import ROOT_PATH


class CorePlugins(object):

    def __init__(self, w3af_core):
        self._w3af_core = w3af_core

        self.initialized = False
        self._plugins_names_dict = None
        self._plugins_options = None
        self.plugins = None
        self.zero_enabled_plugins()

    def zero_enabled_plugins(self):
        """
        Init some internal variables; this method is called when the whole
        process starts, and when the user loads a new profile.
        """
        # A dict with plugin types as keys and a list of plugin names as values
        self._plugins_names_dict = {'audit': [],
                                    'grep': [],
                                    'bruteforce': [],
                                    'crawl': [],
                                    'evasion': [],
                                    'mangle': [],
                                    'output': [],
                                    'auth': [],
                                    'infrastructure': []}

        self._plugins_options = {'audit': {},
                                 'grep': {},
                                 'bruteforce': {},
                                 'crawl': {},
                                 'evasion': {},
                                 'mangle': {},
                                 'output': {},
                                 'attack': {},
                                 'auth': {},
                                 'infrastructure': {}}

        # A dict with plugin types as keys and a list of plugin instances as
        # values
        self.plugins = {'audit': [],
                        'grep': [],
                        'bruteforce': [],
                        'crawl': [],
                        'evasion': [],
                        'mangle': [],
                        'output': [],
                        'auth': [],
                        'infrastructure': []}

        # After we zero all options and enabled plugins we need to call
        # init_plugins again
        self.initialized = False

    def init_plugins(self):
        """
        The user interfaces should run this method *before* calling start().
        If they don't do it, an exception is raised.
        """
        # This is inited before all, to have a full logging support.
        om.manager.set_output_plugins(self._plugins_names_dict['output'])

        # Create an instance of each requested plugin and add it to the plugin
        # list. Plugins are added taking care of plugin dependencies and
        # configuration
        #
        # Create all the plugin instances
        #
        self.plugin_factory()

        #
        # Some extra init steps for mangle plugins
        #
        mangle = self.plugins['mangle']
        self._w3af_core.uri_opener.settings.set_mangle_plugins(mangle)

        # The plugin factory might raise an exception due to invalid plugin
        # configurations. Only set the initialized attribute if we get to the
        # end of init_plugins()
        self.initialized = True

    def set_plugin_options(self, plugin_type, plugin_name, plugin_options):
        """
        :param plugin_type: The plugin type, like 'audit' or 'crawl'
        :param plugin_name: The plugin name, like 'sqli' or 'web_spider'
        :param plugin_options: An OptionList with the option objects for a
                               plugin.

        :return: No value is returned.
        """
        if plugin_type.lower() == 'output':
            om.manager.set_plugin_options(plugin_name, plugin_options)

        # Save the options, even if they are invalid. This is a good idea
        # because:
        #
        #   * If the user sees an error raised by the set_options() below he'll
        #     fix the configuration (calling this method again) and override
        #     the invalid settings
        #
        #   * If the user ignores the error raised by set_options() and tries
        #     to start the scan init_plugins will fail, this is:
        #     https://github.com/andresriancho/w3af/issues/7477
        #
        self._plugins_options[plugin_type][plugin_name] = plugin_options

        # The following lines make sure that the plugin will accept the options
        # that the user is setting
        plugin_inst = self.get_plugin_inst(plugin_type, plugin_name)
        plugin_inst.set_options(plugin_options)

    def get_plugin_options(self, plugin_type, plugin_name):
        """
        Get the options for a plugin.

        IMPORTANT NOTE: This method only returns the options for a plugin
        that was previously configured using set_plugin_options. If you want
        to get the default options for a plugin, get a plugin instance and
        perform a plugin.get_options()

        :return: An OptionList with the plugin options.
        """
        return self._plugins_options.get(plugin_type, {}).get(plugin_name, None)

    def get_all_plugin_options(self):
        return self._plugins_options

    def get_all_enabled_plugins(self):
        return self._plugins_names_dict

    def get_enabled_plugins(self, plugin_type):
        return self._plugins_names_dict[plugin_type]

    def set_plugins(self, plugin_names, plugin_type, raise_on_error=True):
        """
        This method sets the plugins that w3afCore is going to use. Before this
        plugin existed w3afCore used setcrawl_plugins() / setAuditPlugins() /
        etc , this wasn't really extensible and was replaced with a combination
        of set_plugins and get_plugin_types. This way the user interface isn't
        bound to changes in the plugin types that are added or removed.

        :param plugin_names: A list with the names of the Plugins that will be
                             run.
         :param plugin_type: The type of the plugin.

        :return: A list of plugins that are unknown to the framework. This is
                 mainly used to have some error handling related to old profiles
                 that might reference deprecated plugins.
        """
        # Validate the input...
        plugin_names = list(set(plugin_names))
        known_plugin_names = self.get_plugin_list(plugin_type)
        unknown_plugins = []
        
        for plugin_name in plugin_names:
            if plugin_name not in known_plugin_names \
            and plugin_name.replace('!', '') not in known_plugin_names\
            and plugin_name != 'all':
            
                if raise_on_error:
                    raise ValueError('Unknown plugin %s' % plugin_name)
                else:
                    unknown_plugins.append(plugin_name)

        # If we don't raise an error when an unknown plugin name is enabled,
        # at least don't try to call the "_set_plugin_generic" method with it
        plugin_names = [pn for pn in plugin_names if pn not in unknown_plugins]

        set_dict = {
            'crawl': partial(self._set_plugin_generic, 'crawl'),
            'audit': partial(self._set_plugin_generic, 'audit'),
            'grep': partial(self._set_plugin_generic, 'grep'),
            'output': partial(self._set_plugin_generic, 'output'),
            'mangle': partial(self._set_plugin_generic, 'mangle'),
            'bruteforce': partial(self._set_plugin_generic, 'bruteforce'),
            'auth': partial(self._set_plugin_generic, 'auth'),
            'infrastructure': partial(self._set_plugin_generic, 'infrastructure'),
            'evasion': self._set_evasion_plugins,
        }

        set_dict[plugin_type](plugin_names)
        
        return unknown_plugins
    
    def reload_modified_plugin(self, plugin_type, plugin_name):
        """
        When a plugin is modified using the plugin editor, all instances of it
        inside the core have to be "reloaded" so, if the plugin code was changed
        the core reflects that change.

        :param plugin_type: The plugin type of the modified plugin 'audit',
                            'crawl', etc.
        :param plugin_name: The plugin name of the modified plugin 'xss',
                            'sqli', etc
        """
        try:
            amodule = sys.modules['w3af.plugins.%s.%s' % (plugin_type, plugin_name)]
        except KeyError:
            msg = 'Tried to reload a plugin that was never imported! (%s.%s)'
            om.out.debug(msg % (plugin_type, plugin_name))
        else:
            reload(amodule)

    def get_plugin_type_desc(self, plugin_type):
        """
        :param plugin_type: The type of plugin for which we want a description.
        :return: A description of the plugin type passed as parameter
        """
        try:
            __import__('w3af.plugins.%s' % plugin_type)
            a_module = sys.modules['w3af.plugins.%s' % plugin_type]
        except Exception:
            msg = 'Unknown plugin type: "%s".'
            raise BaseFrameworkException(msg % plugin_type)
        else:
            return a_module.get_long_description()

    def get_plugin_types(self):
        """
        :return: A list with all plugin types.
        """
        def rem_from_list(ele, lst):
            try:
                lst.remove(ele)
            except:
                pass
        plugin_types = [x for x in os.listdir(os.path.join(ROOT_PATH, 'plugins'))]
        # Now we filter to show only the directories
        plugin_types = [d for d in plugin_types
                        if os.path.isdir(os.path.join(ROOT_PATH, 'plugins', d))]
        rem_from_list('attack', plugin_types)
        rem_from_list('tests', plugin_types)
        rem_from_list('.git', plugin_types)
        return plugin_types

    def get_plugin_list(self, plugin_type):
        """
        :return: A string list of the names of all available plugins by type.
        """
        str_plugin_list = get_file_list(os.path.join(ROOT_PATH, 'plugins',
                                                     plugin_type))
        return str_plugin_list

    def get_plugin_inst(self, plugin_type, plugin_name):
        """
        :return: An instance of a plugin.
        """
        plugin_inst = factory('w3af.plugins.%s.%s' % (plugin_type, plugin_name))
        plugin_inst.set_url_opener(self._w3af_core.uri_opener)
        plugin_inst.set_worker_pool(self._w3af_core.worker_pool)
        plugin_inst.set_w3af_core(self._w3af_core)
        
        if plugin_name in self._plugins_options[plugin_type].keys():
            custom_options = self._plugins_options[plugin_type][plugin_name]
            plugin_inst.set_options(custom_options)

        # This will init some plugins like mangle and output
        if plugin_type == 'attack' and not self.initialized:
            self.init_plugins()
            
        return plugin_inst

    def get_quick_instance(self, plugin_type, plugin_name):
        plugin_module = '.'.join(['w3af', 'plugins', plugin_type, plugin_name])
        return factory(plugin_module)

    def expand_all(self):
        for plugin_type, enabled_plugins in self._plugins_names_dict.iteritems():
            if 'all' in enabled_plugins:
                file_list = [f for f in os.listdir(
                    os.path.join(ROOT_PATH, 'plugins', plugin_type))]
                all_plugins = [os.path.splitext(f)[0] for f in file_list
                               if os.path.splitext(f)[1] == '.py']
                all_plugins.remove('__init__')

                enabled_plugins.extend(all_plugins)
                enabled_plugins = list(set(enabled_plugins))
                enabled_plugins.remove('all')
                self._plugins_names_dict[plugin_type] = enabled_plugins

    def remove_exclusions(self):
        for plugin_type, enabled_plugins in self._plugins_names_dict.iteritems():
            for plugin_name in enabled_plugins[:]:
                if plugin_name.startswith('!'):
                    enabled_plugins.remove(plugin_name)
                    enabled_plugins.remove(plugin_name.replace('!', ''))

    def resolve_dependencies(self):
        for plugin_type, enabled_plugins in self._plugins_names_dict.iteritems():
            for plugin_name in enabled_plugins:

                plugin_inst = self.get_quick_instance(plugin_type, plugin_name)

                for dep in plugin_inst.get_plugin_deps():

                    try:
                        dep_plugin_type, dep_plugin_name = dep.split('.')
                    except:
                        msg = ('Plugin dependencies must be indicated using'
                               ' plugin_type.plugin_name notation. This is'
                               ' an error in %s.get_plugin_deps().' % plugin_name)
                        raise BaseFrameworkException(msg)

                    if dep_plugin_name not in self._plugins_names_dict[dep_plugin_type]:
                        om.out.information('Enabling %s\'s dependency %s' %
                                           (plugin_name, dep_plugin_name))

                        self._plugins_names_dict[
                            dep_plugin_type].append(dep_plugin_name)

                        self.resolve_dependencies()

    def order_plugins(self):
        """
        Makes sure that dependencies are run before the plugin that
        required it
        """
        plugin_names = self._plugins_names_dict

        for plugin_type, enabled_plugins in plugin_names.iteritems():
            for plugin_name in enabled_plugins:
                plugin_inst = self.get_quick_instance(plugin_type, plugin_name)

                for dep in plugin_inst.get_plugin_deps():
                    dep_plugin_type, dep_name = dep.split('.')

                    if dep_plugin_type != plugin_type:
                        # We can't guarantee execution order if the plugin
                        # dependencies are of different types
                        continue

                    try:
                        plugin_index = plugin_names[plugin_type].index(plugin_name)
                        dependency_index = plugin_names[plugin_type].index(dep_name)
                    except ValueError:
                        # A very rare case which I was unable to reproduce since
                        # it requires the enabled_plugins list to change
                        # during our iteration
                        #
                        # ValueError: 'detect_reverse_proxy' is not in list
                        # https://github.com/andresriancho/w3af/issues/11062
                        continue

                    if dependency_index < plugin_index:
                        # Everything is ok, the dependency is run before the
                        # plugin that requires it
                        continue

                    # Switch
                    plugin_names[plugin_type][plugin_index] = dep_name
                    plugin_names[plugin_type][dependency_index] = plugin_name

    def create_instances(self):
        for plugin_type, enabled_plugins in self._plugins_names_dict.iteritems():
            for plugin_name in enabled_plugins:
                plugin_instance = self.get_plugin_inst(plugin_type,
                                                       plugin_name)
                if plugin_instance not in self.plugins[plugin_type]:
                    self.plugins[plugin_type].append(plugin_instance)
                else:
                    # Ensure that the latest settings are applied to the instance
                    # that will be used for execution
                    for existing_inst in self.plugins[plugin_type]:
                        if existing_inst.get_name() == plugin_name and plugin_name in self._plugins_options[plugin_type].keys():
                            custom_options = self._plugins_options[plugin_type][plugin_name]
                            existing_inst.set_options(custom_options)


    def plugin_factory(self):
        """
        This method creates the user requested plugins.

        :return: A list with plugins to be executed, this list is ordered using
                 the exec priority.
        """
        self.expand_all()
        self.remove_exclusions()
        self.resolve_dependencies()

        # Now the self._plugins_names_dict has all the plugin names that
        # we should enable, for all types, but in the incorrect order:
        # without taking care of dependencies
        self.order_plugins()
        self.create_instances()

    def _set_plugin_generic(self, plugin_type, plugin_list):
        """
        :param plugin_type: The plugin type where to store the @plugin_list.
        :param plugin_list: A list with the names of @plugin_type plugins to be
                            run.
        """
        self._plugins_names_dict[plugin_type] = plugin_list

    def _set_evasion_plugins(self, evasion_plugins):
        """
        :param evasion_plugins: A list with the names of Evasion Plugins that
                                will be used.
        :return: No value is returned.
        """
        self._plugins_names_dict['evasion'] = evasion_plugins
        self.plugin_factory()

        self._w3af_core.uri_opener.set_evasion_plugins(self.plugins['evasion'])
