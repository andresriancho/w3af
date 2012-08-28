'''
basic.py

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

import unittest

from core.controllers.w3afCore import w3afCore
from core.controllers.w3afException import w3afException

from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.plugins.auth_plugin import AuthPlugin
from core.controllers.plugins.bruteforce_plugin import BruteforcePlugin
from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.plugins.evasion_plugin import EvasionPlugin
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.plugins.mangle_plugin import ManglePlugin
from core.controllers.plugins.output_plugin import OutputPlugin

from plugins.tests.helper import PluginTest, PluginConfig

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

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.w3afcore = w3afCore()
        
        self.plugin_types = self.w3afcore.plugins.get_plugin_types()
        self.plugin_types += ['attack']
        self.plugins = {}
        
        for plugin_type in self.plugin_types:
            self.plugins[plugin_type] = []
            for plugin_name in self.w3afcore.plugins.get_plugin_list( plugin_type ): 
                plugin = self.w3afcore.plugins.get_plugin_inst(plugin_type, plugin_name)
                self.plugins[plugin_type].append( plugin )
            
    def test_plugin_options(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                opt1 = plugin.get_options()

    def test_plugin_deps(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                dependencies = plugin.get_plugin_deps()
                self.assertTrue( isinstance(dependencies, list) )
                
                for dep in dependencies:
                    self.assertTrue( isinstance(dep, basestring) )
                    plugin_type, plugin_name = dep.split('.')
                    
                    self.assertTrue( plugin_type in self.w3afcore.plugins.get_plugin_types() )
                    
                    msg = '%s is not of type %s in %s plugin dependency.' % (plugin_name, plugin_type, plugin)
                    self.assertTrue( plugin_name in self.w3afcore.plugins.get_plugin_list( plugin_type ), msg )
                
    def test_plugin_desc(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                self.assertTrue( isinstance(plugin.get_plugin_deps(), list) )
                
                self.assertTrue( isinstance( plugin.get_long_desc(), basestring) )
                
                self.assertTrue( isinstance( plugin.getDesc(), basestring) )
                msg = 'Description for %s.%s is too short'
                self.assertGreater( len(plugin.getDesc()), 20, msg % (plugin_type, plugin) )
                
    def test_plugin_root_probability(self):
        for plugin in self.plugins['attack']:
            plugin.getRootProbability()
        
    def test_plugin_type_description(self):
        for plugin_type in self.w3afcore.plugins.get_plugin_types():
            self.w3afcore.plugins.get_plugin_type_desc(plugin_type)
    
    def test_plugin_is_of_correct_type(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                msg = '%s if not of expected type %s' % (plugin,PLUGIN_TYPES[plugin_type])
                self.assertTrue( isinstance(plugin, PLUGIN_TYPES[plugin_type]), msg )
                
                self.assertEqual( plugin.getType(), plugin_type, msg )


class TestFailOnInvalidURL(PluginTest):
    
    _run_configs = {
        'cfg': {
                'target': None,
                'plugins': {'infrastructure': (PluginConfig('hmap'),)}
                }
        }
    
    def test_fail_1(self):
        cfg = self._run_configs['cfg']
        self.assertRaises(w3afException, self._scan, 'http://http://moth/', cfg['plugins'])

    def test_fail_2(self):
        cfg = self._run_configs['cfg']
        self.assertRaises(w3afException, self._scan, '', cfg['plugins'])
