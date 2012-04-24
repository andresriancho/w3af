# -*- coding: UTF-8 -*-
'''
test_plugins.py

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


class Test_w3afCore_plugins(unittest.TestCase):

    def setUp(self):
        pass
    
    def test_getPluginTypes(self):
        w3af_core = w3afCore()
        plugin_types = w3af_core.plugins.getPluginTypes()
        expected = ['grep', 'output', 'mangle', 'audit', 'discovery',
                    'evasion', 'bruteforce', 'auth']
        self.assertEquals( plugin_types, expected )
        
    def test_getPluginList(self):
        w3af_core = w3afCore()
        plugin_list = w3af_core.plugins.getPluginList('audit')

        expected = ['sqli', 'xss', 'eval']
        for plugin_name in expected:
            self.assertTrue( plugin_name in plugin_list )   

    def test_getPluginInstance(self):
        w3af_core = w3afCore()
        plugin_inst = w3af_core.plugins.getPluginInstance('sqli','audit')

        self.assertEquals( plugin_inst.getName(), 'sqli' )

    def test_setPlugins(self):
        w3af_core = w3afCore()
        enabled = ['sqli']
        w3af_core.plugins.setPlugins(enabled,'audit')
        retrieved = w3af_core.plugins.getEnabledPlugins('audit')
        self.assertEquals( enabled, retrieved )

    def test_getAllEnabledPlugins(self):
        w3af_core = w3afCore()
        enabled_audit = ['sqli', 'xss']
        enabled_grep = ['privateIP']
        w3af_core.plugins.setPlugins(enabled_audit,'audit')
        w3af_core.plugins.setPlugins(enabled_grep,'grep')
        
        all_enabled = w3af_core.plugins.getAllEnabledPlugins()
        
        self.assertEquals( enabled_audit, all_enabled['audit'] )
        self.assertEquals( enabled_grep, all_enabled['grep'] )
    
    def test_plugin_options(self):
        w3af_core = w3afCore()
        plugin_inst = w3af_core.plugins.getPluginInstance('webSpider','discovery')
        options_1 = plugin_inst.getOptions()
        
        w3af_core.plugins.setPluginOptions('discovery', 'webSpider', options_1)
        options_2 = w3af_core.plugins.getPluginOptions('discovery', 'webSpider')
        
        self.assertEquals( options_1, options_2 )
    
    def test_plugin_options_invalid(self):
        w3af_core = w3afCore()
        self.assertRaises(TypeError, w3af_core.plugins.setPluginOptions, 'discovery', 'webSpider', None)
        
    def test_init_plugins(self):
        w3af_core = w3afCore()
        enabled = ['webSpider']
        w3af_core.plugins.setPlugins(enabled,'discovery')
        w3af_core.plugins.init_plugins()
        
        self.assertEquals( len(w3af_core.plugins.plugins['discovery']), 1 )
        
        plugin_inst = w3af_core.plugins.plugins['discovery'][0]
        self.assertEquals( plugin_inst.getName(), 'webSpider' )
                