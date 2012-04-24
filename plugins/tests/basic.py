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


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.w3afcore = w3afCore()
        
        self.plugin_types = self.w3afcore.plugins.getPluginTypes()
        self.plugin_types += ['attack']
        self.plugins = []
        
        for plugin_type in self.plugin_types:
            for plugin_name in self.w3afcore.plugins.getPluginList( plugin_type ): 
                plugin = self.w3afcore.plugins.getPluginInstance(plugin_name, plugin_type)
                self.plugins.append(plugin)
            
    def test_plugin_options(self):
        for plugin in self.plugins:
            opt1 = plugin.getOptions()

    def test_plugin_deps_desc(self):
        for plugin in self.plugins:
            plugin.getPluginDeps()
            plugin.getLongDesc()
                
    def test_plugin_root_probability(self):
        for plugin in self.plugins:
            if plugin.getType() == 'attack':
                plugin.getRootProbability()

                
