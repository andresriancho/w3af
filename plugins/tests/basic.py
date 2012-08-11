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

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.basePlugin.baseAuthPlugin import baseAuthPlugin
from core.controllers.basePlugin.baseBruteforcePlugin import baseBruteforcePlugin
from core.controllers.basePlugin.baseCrawlPlugin import baseCrawlPlugin
from core.controllers.basePlugin.baseEvasionPlugin import baseEvasionPlugin
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.controllers.basePlugin.baseInfrastructurePlugin import baseInfrastructurePlugin
from core.controllers.basePlugin.baseManglePlugin import baseManglePlugin
from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin

PLUGIN_TYPES = {'attack': baseAttackPlugin,
                'audit': baseAuditPlugin,
                'auth': baseAuthPlugin,
                'bruteforce': baseBruteforcePlugin,
                'crawl': baseCrawlPlugin,
                'evasion': baseEvasionPlugin,
                'grep': baseGrepPlugin,
                'infrastructure': baseInfrastructurePlugin,
                'mangle': baseManglePlugin,
                'output': baseOutputPlugin}

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.w3afcore = w3afCore()
        
        self.plugin_types = self.w3afcore.plugins.getPluginTypes()
        self.plugin_types += ['attack']
        self.plugins = {}
        
        for plugin_type in self.plugin_types:
            self.plugins[plugin_type] = []
            for plugin_name in self.w3afcore.plugins.getPluginList( plugin_type ): 
                plugin = self.w3afcore.plugins.getPluginInstance(plugin_name, plugin_type)
                self.plugins[plugin_type].append( plugin )
            
    def test_plugin_options(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                opt1 = plugin.getOptions()

    def test_plugin_deps(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                dependencies = plugin.getPluginDeps()
                self.assertTrue( isinstance(dependencies, list) )
                
                for dep in dependencies:
                    self.assertTrue( isinstance(dep, basestring) )
                    plugin_type, plugin_name = dep.split('.')
                    
                    self.assertTrue( plugin_type in self.w3afcore.plugins.getPluginTypes() )
                    
                    msg = '%s is not of type %s in %s plugin dependency.' % (plugin_name, plugin_type, plugin)
                    self.assertTrue( plugin_name in self.w3afcore.plugins.getPluginList( plugin_type ), msg )
                
    def test_plugin_desc(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                self.assertTrue( isinstance(plugin.getPluginDeps(), list) )
                
                self.assertTrue( isinstance( plugin.getLongDesc(), basestring) )
                
                self.assertTrue( isinstance( plugin.getDesc(), basestring) )
                msg = 'Description for %s.%s is too short'
                self.assertGreater( len(plugin.getDesc()), 20, msg % (plugin_type, plugin) )
                
    def test_plugin_root_probability(self):
        for plugin in self.plugins['attack']:
            plugin.getRootProbability()
        
    def test_plugin_type_description(self):
        for plugin_type in self.w3afcore.plugins.getPluginTypes():
            self.w3afcore.plugins.getPluginTypesDesc(plugin_type)
    
    def test_plugin_is_of_correct_type(self):
        for plugin_type in self.plugins:
            for plugin in self.plugins[plugin_type]:
                msg = '%s if not of expected type %s' % (plugin,PLUGIN_TYPES[plugin_type])
                self.assertTrue( isinstance(plugin, PLUGIN_TYPES[plugin_type]), msg )
                
                self.assertEqual( plugin.getType(), plugin_type, msg )

                
