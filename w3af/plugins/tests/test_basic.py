"""
basic.py

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
import unittest
import os

from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.plugins.mangle_plugin import ManglePlugin
from w3af.core.controllers.plugins.output_plugin import OutputPlugin

from w3af.core.data.options.option_types import (
    BOOL, INT, FLOAT, STRING, URL, IPPORT, LIST,
    REGEX, COMBO, INPUT_FILE, OUTPUT_FILE, PORT, IP,
    QUERY_STRING, HEADER)

from w3af.plugins.tests.helper import PluginTest, PluginConfig

PLUGIN_TYPES = {'attack': AttackPlugin,
                'audit': AuditPlugin,
                'auth': AuthPlugin,
                'bruteforce': BruteforcePlugin,
                'crawl': CrawlPlugin,
                'evasion': EvasionPlugin,
                'grep': GrepPlugin,
                'infrastructure': InfrastructurePlugin,
                'mangle': ManglePlugin,
                'output': OutputPlugin}


@attr('smoke')
class TestBasic(unittest.TestCase):

    def setUp(self):
        self.w3afcore = w3afCore()

        self.plugin_types = self.w3afcore.plugins.get_plugin_types()
        self.plugin_types += ['attack']
        self.plugins = {}

        for plugin_type in self.plugin_types:
            self.plugins[plugin_type] = []
            for plugin_name in self.w3afcore.plugins.get_plugin_list(plugin_type):
                plugin = self.w3afcore.plugins.get_plugin_inst(
                    plugin_type, plugin_name)
                self.plugins[plugin_type].append(plugin)

    def test_plugin_options(self):

        OPTION_TYPES = (
            BOOL, INT, FLOAT, STRING, URL, IPPORT, LIST, REGEX, COMBO,
            INPUT_FILE, OUTPUT_FILE, PORT, IP, QUERY_STRING, HEADER)

        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                opt_lst = plugin.get_options()

                for opt in opt_lst:
                    self.assertIn(opt.get_type(), OPTION_TYPES)
                    self.assertTrue(opt.get_name())
                    self.assertEqual(opt, opt)

                    # Just verify that this doesn't crash and that the types
                    # are correct
                    self.assertIsInstance(opt.get_name(), basestring)
                    self.assertIsInstance(opt.get_desc(), basestring)
                    self.assertIsInstance(opt.get_type(), basestring)
                    self.assertIsInstance(opt.get_help(), basestring)
                    self.assertIsInstance(opt.get_value_str(), basestring)

    def test_plugin_deps(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                dependencies = plugin.get_plugin_deps()
                self.assertTrue(isinstance(dependencies, list))

                for dep in dependencies:
                    self.assertTrue(isinstance(dep, basestring))
                    plugin_type, plugin_name = dep.split('.')

                    self.assertTrue(plugin_type in self.w3afcore.plugins.get_plugin_types())

                    msg = '%s is not of type %s in %s plugin dependency.' % (
                        plugin_name, plugin_type, plugin)
                    self.assertIn(plugin_name,
                                  self.w3afcore.plugins.get_plugin_list(plugin_type),
                                  msg)

    def test_plugin_desc(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                self.assertTrue(isinstance(plugin.get_plugin_deps(), list))

                
                self.assertTrue(isinstance(plugin.get_desc(), basestring))
                msg = 'Description "%s" (len:%s) for %s.%s is too short'
                self.assertGreaterEqual(len(plugin.get_desc()), 20,
                                        msg % (plugin.get_desc(),
                                               len(plugin.get_desc()),
                                               plugin_type,
                                               plugin.get_name()))
                
                self.assertTrue(isinstance(plugin.get_long_desc(), basestring))
                
                msg = 'Long description "%s" for %s.%s is too short'
                self.assertGreater(len(plugin.get_long_desc()), 50,
                                   msg % (plugin.get_long_desc(),
                                          plugin_type,
                                          plugin.get_name()))

    def test_plugin_root_probability(self):
        for plugin in self.plugins['attack']:
            plugin.get_root_probability()

    def test_plugin_type_description(self):
        for plugin_type in self.w3afcore.plugins.get_plugin_types():
            self.w3afcore.plugins.get_plugin_type_desc(plugin_type)

    def test_no_kb_access_from_plugin(self):
        audit_path = os.path.join(ROOT_PATH, 'plugins', 'audit')
        
        for audit_plugin in os.listdir(audit_path):
            if not audit_plugin.endswith('.py'):
                continue
            
            joined_entry = os.path.join(ROOT_PATH, 'plugins', 'audit',
                                        audit_plugin)
            
            if os.path.isdir(joined_entry):
                continue
            
            plugin_code = file(joined_entry).read()
            
            if 'kb.kb.append' in plugin_code:
                msg = '%s plugin is directly writing to the kb instead of'\
                      ' going through kb_append_uniq or kb_append.'
                self.assertTrue(False, msg % audit_plugin)
        
    def test_plugin_is_of_correct_type(self):
        
        def defined_in_subclass(klass, attr):
            any_klass_method = getattr(klass, attr, None)
            
            if any_klass_method is None:
                # Not defined in class or parent class
                return False
            
            for base_klass in klass.__class__.__bases__:
                
                base_method = getattr(base_klass, attr, None)
                if base_method is None:
                    # In some cases one of the base classes does not
                    # implement all methods
                    continue
                
                if any_klass_method.__func__ is not base_method.__func__:
                    return True
                
            return False
        
        
        ALL_TYPES_ATTRS = ('_uri_opener', 'output_queue', '_plugin_lock',
                           'get_type')
        
        TYPES_AND_ATTRS = {'attack': ['_generate_shell', 'get_attack_type',
                                      'get_root_probability', 'get_kb_location'],
                           'audit': ['audit',],
                           'auth': ['login', 'logout', 'has_active_session'],
                           'bruteforce': ['audit',],
                           'crawl': ['crawl'],
                           'evasion': ['get_priority', 'modify_request'],
                           'grep': ['grep'],
                           'infrastructure': ['discover',],
                           'mangle': ['mangle_request', 'mangle_response'],
                           'output': ['debug', 'information', 'error',
                                      'vulnerability', 'console']}
        
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                
                ptype = PLUGIN_TYPES[plugin_type]
                msg = '%s is not of expected type %s' % (plugin, ptype)
                
                self.assertTrue(isinstance(plugin, ptype), msg)
                self.assertEqual(plugin.get_type(), plugin_type, msg)

                # Also assert that the plugin called <Type>Plugin.__init__(self)
                # and that the corresponding attrs are there
                for attr in ALL_TYPES_ATTRS:
                    msg = 'Plugin %s doesn\'t have attribute %s: %r' % (plugin.get_name(),
                                                                     attr,
                                                                     dir(plugin))
                    self.assertTrue(getattr(plugin, attr, False) != False, msg)
                
                # Verify that the current plugin, and not the parent, defined
                # the required methods
                for attr in TYPES_AND_ATTRS[plugin.get_type()]:
                    msg = 'Plugin %s doesn\'t have attribute %s.' % (plugin.get_name(), attr)
                    self.assertTrue(defined_in_subclass(plugin, attr), msg)


class TestFailOnInvalidURL(PluginTest):

    _run_configs = {
        'cfg': {
        'target': None,
        'plugins': {'infrastructure': (PluginConfig('hmap'),)}
        }
    }

    def test_fail_1(self):
        cfg = self._run_configs['cfg']
        self.assertRaises(ValueError,
                          self._scan, 'http://http://moth/', cfg['plugins'],
                          verify_targets=False)

    def test_fail_2(self):
        cfg = self._run_configs['cfg']
        self.assertRaises(ValueError, self._scan, '', cfg['plugins'],
                          verify_targets=False)
