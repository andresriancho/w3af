# -*- coding: UTF-8 -*-
"""
test_plugins.py

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
import itertools

from nose.plugins.attrib import attr

from w3af.core.controllers.w3afCore import w3afCore


@attr('smoke')
class Test_w3afCore_plugins(unittest.TestCase):

    def test_get_plugin_types(self):
        w3af_core = w3afCore()
        plugin_types = w3af_core.plugins.get_plugin_types()
        expected = set(['grep', 'output', 'mangle', 'audit', 'crawl',
                        'evasion', 'bruteforce', 'auth', 'infrastructure'])
        self.assertEquals(set(plugin_types), expected)

    def test_get_plugin_listAudit(self):
        w3af_core = w3afCore()
        plugin_list = w3af_core.plugins.get_plugin_list('audit')

        expected = set(['sqli', 'xss', 'eval'])
        self.assertTrue(set(plugin_list).issuperset(expected))

    def test_get_plugin_listCrawl(self):
        w3af_core = w3afCore()
        plugin_list = w3af_core.plugins.get_plugin_list('crawl')

        expected = set(['web_spider', 'spider_man'])
        self.assertTrue(set(plugin_list).issuperset(expected))

    def test_get_plugin_inst(self):
        w3af_core = w3afCore()
        plugin_inst = w3af_core.plugins.get_plugin_inst('audit', 'sqli')

        self.assertEquals(plugin_inst.get_name(), 'sqli')

    def test_get_plugin_instAll(self):
        w3af_core = w3afCore()

        for plugin_type in itertools.chain(w3af_core.plugins.get_plugin_types(), ['attack']):
            for plugin_name in w3af_core.plugins.get_plugin_list(plugin_type):
                plugin_inst = w3af_core.plugins.get_plugin_inst(
                    plugin_type, plugin_name)
                self.assertEquals(plugin_inst.get_name(), plugin_name)

    def test_set_plugins(self):
        w3af_core = w3afCore()
        enabled = ['sqli', ]
        w3af_core.plugins.set_plugins(enabled, 'audit')
        retrieved = w3af_core.plugins.get_enabled_plugins('audit')
        self.assertEquals(enabled, retrieved)

    def test_set_plugins_negative(self):
        w3af_core = w3afCore()
        enabled = ['fake', ]
        self.assertRaises(ValueError, w3af_core.plugins.set_plugins, enabled, 'output')

    def test_set_plugins_negative_without_raise(self):
        w3af_core = w3afCore()
        enabled = ['fake', ]
        unknown_plugins = w3af_core.plugins.set_plugins(enabled, 'output', raise_on_error=False)
        self.assertEqual(enabled, unknown_plugins)
        w3af_core.plugins.init_plugins()

    def test_get_all_enabled_plugins(self):
        w3af_core = w3afCore()
        enabled_audit = ['sqli', 'xss']
        enabled_grep = ['private_ip']
        w3af_core.plugins.set_plugins(enabled_audit, 'audit')
        w3af_core.plugins.set_plugins(enabled_grep, 'grep')

        all_enabled = w3af_core.plugins.get_all_enabled_plugins()

        self.assertEquals(enabled_audit, all_enabled['audit'])
        self.assertEquals(enabled_grep, all_enabled['grep'])

    def test_plugin_options(self):
        w3af_core = w3afCore()
        plugin_inst = w3af_core.plugins.get_plugin_inst('crawl', 'web_spider')
        options_1 = plugin_inst.get_options()

        w3af_core.plugins.set_plugin_options('crawl', 'web_spider', options_1)
        options_2 = w3af_core.plugins.get_plugin_options('crawl', 'web_spider')

        self.assertEquals(options_1, options_2)

    def test_plugin_options_invalid(self):
        w3af_core = w3afCore()
        self.assertRaises(TypeError, w3af_core.plugins.set_plugin_options,
                          'crawl', 'web_spider', None)

    def test_init_plugins(self):
        w3af_core = w3afCore()
        enabled = ['web_spider']
        w3af_core.plugins.set_plugins(enabled, 'crawl')
        w3af_core.plugins.init_plugins()

        self.assertEquals(len(w3af_core.plugins.plugins['crawl']), 1,
                          w3af_core.plugins.plugins['crawl'])

        plugin_inst = list(w3af_core.plugins.plugins['crawl'])[0]
        self.assertEquals(plugin_inst.get_name(), 'web_spider')

    def test_enable_all(self):
        w3af_core = w3afCore()
        enabled = ['all']
        w3af_core.plugins.set_plugins(enabled, 'crawl')
        w3af_core.plugins.init_plugins()

        self.assertEquals(set(w3af_core.plugins.get_enabled_plugins('crawl')),
                          set(w3af_core.plugins.get_plugin_list('crawl')))

        self.assertEquals(len(w3af_core.plugins.get_enabled_plugins('crawl')),
                          len(w3af_core.plugins.get_plugin_list('crawl')))

    def test_enable_all_but_web_spider(self):
        w3af_core = w3afCore()
        enabled = ['all', '!web_spider']
        w3af_core.plugins.set_plugins(enabled, 'crawl')
        w3af_core.plugins.init_plugins()

        all_plugins = w3af_core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')

        self.assertEquals(set(w3af_core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_all_but_two(self):
        w3af_core = w3afCore()
        enabled = ['all', '!web_spider', '!archive_dot_org']
        w3af_core.plugins.set_plugins(enabled, 'crawl')
        w3af_core.plugins.init_plugins()

        all_plugins = w3af_core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')
        all_plugins.remove('archive_dot_org')

        self.assertEquals(set(w3af_core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_not_web_spider_all(self):
        w3af_core = w3afCore()
        enabled = ['!web_spider', 'all']
        w3af_core.plugins.set_plugins(enabled, 'crawl')
        w3af_core.plugins.init_plugins()

        all_plugins = w3af_core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')

        self.assertEquals(set(w3af_core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_dependency_same_type(self):
        w3af_core = w3afCore()
        enabled_infra = ['php_eggs', ]
        w3af_core.plugins.set_plugins(enabled_infra, 'infrastructure')
        w3af_core.plugins.init_plugins()

        enabled_infra.append('server_header')

        self.assertEquals(
            set(w3af_core.plugins.get_enabled_plugins('infrastructure')),
            set(enabled_infra))

    def test_enable_dependency_same_type_order(self):
        w3af_core = w3afCore()
        enabled_infra = ['php_eggs', ]
        w3af_core.plugins.set_plugins(enabled_infra, 'infrastructure')
        w3af_core.plugins.init_plugins()

        self.assertEqual(w3af_core.plugins.get_enabled_plugins(
            'infrastructure').index('server_header'), 0)
        self.assertEqual(w3af_core.plugins.get_enabled_plugins(
            'infrastructure').index('php_eggs'), 1)

        self.assertEqual(w3af_core.plugins.plugins[
                         'infrastructure'][0].get_name(), 'server_header')
        self.assertEqual(w3af_core.plugins.plugins[
                         'infrastructure'][1].get_name(), 'php_eggs')

    def test_enable_dependency_different_type(self):
        w3af_core = w3afCore()
        enabled_crawl = ['url_fuzzer', ]
        w3af_core.plugins.set_plugins(enabled_crawl, 'crawl')

        enabled_infra = ['allowed_methods', ]

        w3af_core.plugins.init_plugins()

        self.assertEquals(set(w3af_core.plugins.get_enabled_plugins('crawl')),
                          set(enabled_crawl))

        self.assertEquals(
            set(w3af_core.plugins.get_enabled_plugins('infrastructure')),
            set(enabled_infra))

    def test_enable_all_all(self):
        w3af_core = w3afCore()
        for plugin_type in w3af_core.plugins.get_plugin_types():
            w3af_core.plugins.set_plugins(['all', ], plugin_type)
        w3af_core.plugins.init_plugins()

        for plugin_type in w3af_core.plugins.get_plugin_types():
            enabled_plugins = w3af_core.plugins.get_enabled_plugins(
                plugin_type)
            all_plugins = w3af_core.plugins.get_plugin_list(plugin_type)
            self.assertEqual(set(enabled_plugins), set(all_plugins))
            self.assertEqual(len(enabled_plugins), len(all_plugins))
