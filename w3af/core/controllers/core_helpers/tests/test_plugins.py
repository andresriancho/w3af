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

from os import listdir as orig_listdir
from nose.plugins.attrib import attr
from mock import patch

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import BaseFrameworkException

TEST_PLUGIN_NAME = 'failing_spider'


@attr('smoke')
class TestW3afCorePlugins(unittest.TestCase):

    def setUp(self):
        super(TestW3afCorePlugins, self).setUp()

        self.listdir_patch = patch('os.listdir')
        self.listdir_mock = self.listdir_patch.start()
        self.listdir_mock.side_effect = listdir_remove_fs

        self.core = w3afCore()

    def tearDown(self):
        super(TestW3afCorePlugins, self).tearDown()

        self.listdir_patch.stop()
        self.core.worker_pool.terminate_join()

    def test_get_plugin_types(self):
        plugin_types = self.core.plugins.get_plugin_types()
        expected = {'grep', 'output', 'mangle', 'audit', 'crawl', 'evasion',
                    'bruteforce', 'auth', 'infrastructure'}
        self.assertEquals(set(plugin_types), expected)

    def test_get_plugin_list_audit(self):
        plugin_list = self.core.plugins.get_plugin_list('audit')

        expected = {'sqli', 'xss', 'eval'}
        self.assertTrue(set(plugin_list).issuperset(expected))

    def test_get_plugin_list_crawl(self):
        plugin_list = self.core.plugins.get_plugin_list('crawl')

        expected = {'web_spider', 'spider_man'}
        self.assertTrue(set(plugin_list).issuperset(expected))

    def test_get_plugin_inst(self):
        plugin_inst = self.core.plugins.get_plugin_inst('audit', 'sqli')

        self.assertEquals(plugin_inst.get_name(), 'sqli')

    def test_get_plugin_inst_all(self):
        for plugin_type in itertools.chain(self.core.plugins.get_plugin_types(), ['attack']):
            for plugin_name in self.core.plugins.get_plugin_list(plugin_type):
                plugin_inst = self.core.plugins.get_plugin_inst(
                    plugin_type, plugin_name)
                self.assertEquals(plugin_inst.get_name(), plugin_name)

    def test_set_plugins(self):
        enabled = ['sqli', ]
        self.core.plugins.set_plugins(enabled, 'audit')
        retrieved = self.core.plugins.get_enabled_plugins('audit')
        self.assertEquals(enabled, retrieved)

    def test_set_plugins_negative(self):
        enabled = ['fake', ]
        self.assertRaises(ValueError, self.core.plugins.set_plugins, enabled, 'output')

    def test_set_plugins_negative_without_raise(self):
        enabled = ['fake', ]
        unknown_plugins = self.core.plugins.set_plugins(enabled, 'output',
                                                        raise_on_error=False)
        self.assertEqual(enabled, unknown_plugins)
        self.core.plugins.init_plugins()

    def test_get_all_enabled_plugins(self):
        enabled_audit = ['sqli', 'xss']
        enabled_grep = ['private_ip']
        self.core.plugins.set_plugins(enabled_audit, 'audit')
        self.core.plugins.set_plugins(enabled_grep, 'grep')

        all_enabled = self.core.plugins.get_all_enabled_plugins()

        self.assertEquals(enabled_audit, all_enabled['audit'])
        self.assertEquals(enabled_grep, all_enabled['grep'])

    def test_plugin_options(self):
        plugin_inst = self.core.plugins.get_plugin_inst('crawl', 'web_spider')
        options_1 = plugin_inst.get_options()

        self.core.plugins.set_plugin_options('crawl', 'web_spider', options_1)
        options_2 = self.core.plugins.get_plugin_options('crawl', 'web_spider')

        self.assertEquals(options_1, options_2)

    def test_plugin_options_invalid(self):
        self.assertRaises(TypeError, self.core.plugins.set_plugin_options,
                          'crawl', 'web_spider', None)

    def test_plugin_options_partially_invalid_scan_does_not_start(self):
        self.core.plugins.set_plugins(['generic'], 'auth')

        plugin_inst = self.core.plugins.get_plugin_inst('auth', 'generic')
        options = plugin_inst.get_options()

        username = options['username']
        username.set_value('andres')

        password = options['password']
        password.set_value('foobar')

        # There are missing configuration parameters, so it's ok for this to
        # fail
        self.assertRaises(BaseFrameworkException,
                          self.core.plugins.set_plugin_options,
                          'auth', 'generic', options)

        # Do not start the scan if the user failed to configure the plugins
        # https://github.com/andresriancho/w3af/issues/7477
        self.assertRaises(BaseFrameworkException,
                          self.core.plugins.init_plugins)

        # Now we set all the options again and it should succeed
        options['username_field'].set_value('username')
        options['password_field'].set_value('password')
        options['auth_url'].set_value('http://login.com/')
        options['check_url'].set_value('http://check.com/')
        options['check_string'].set_value('abc')

        self.core.plugins.set_plugin_options('auth', 'generic', options)
        self.core.plugins.init_plugins()

    def test_init_plugins(self):
        enabled = ['web_spider']
        self.core.plugins.set_plugins(enabled, 'crawl')
        self.core.plugins.init_plugins()

        self.assertEquals(len(self.core.plugins.plugins['crawl']), 1,
                          self.core.plugins.plugins['crawl'])

        plugin_inst = list(self.core.plugins.plugins['crawl'])[0]
        self.assertEquals(plugin_inst.get_name(), 'web_spider')

    def test_enable_all(self):
        enabled = ['all']
        self.core.plugins.set_plugins(enabled, 'crawl')
        self.core.plugins.init_plugins()

        self.assertEquals(set(self.core.plugins.get_enabled_plugins('crawl')),
                          set(self.core.plugins.get_plugin_list('crawl')))

        self.assertEquals(len(set(self.core.plugins.get_enabled_plugins('crawl'))),
                          len(set(self.core.plugins.get_plugin_list('crawl'))))

    def test_enable_all_but_web_spider(self):
        enabled = ['all', '!web_spider']
        self.core.plugins.set_plugins(enabled, 'crawl')
        self.core.plugins.init_plugins()

        all_plugins = self.core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')

        self.assertEquals(set(self.core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_all_but_two(self):
        enabled = ['all', '!web_spider', '!archive_dot_org']
        self.core.plugins.set_plugins(enabled, 'crawl')
        self.core.plugins.init_plugins()

        all_plugins = self.core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')
        all_plugins.remove('archive_dot_org')

        self.assertEquals(set(self.core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_not_web_spider_all(self):
        enabled = ['!web_spider', 'all']
        self.core.plugins.set_plugins(enabled, 'crawl')
        self.core.plugins.init_plugins()

        all_plugins = self.core.plugins.get_plugin_list('crawl')
        all_plugins = all_plugins[:]
        all_plugins.remove('web_spider')

        self.assertEquals(set(self.core.plugins.get_enabled_plugins('crawl')),
                          set(all_plugins))

    def test_enable_dependency_same_type(self):
        enabled_infra = ['php_eggs', ]
        self.core.plugins.set_plugins(enabled_infra, 'infrastructure')
        self.core.plugins.init_plugins()

        enabled_infra.append('server_header')

        self.assertEquals(
            set(self.core.plugins.get_enabled_plugins('infrastructure')),
            set(enabled_infra))

    def test_enable_dependency_same_type_order(self):
        enabled_infra = ['php_eggs', ]
        self.core.plugins.set_plugins(enabled_infra, 'infrastructure')
        self.core.plugins.init_plugins()

        self.assertEqual(self.core.plugins.get_enabled_plugins(
            'infrastructure').index('server_header'), 0)
        self.assertEqual(self.core.plugins.get_enabled_plugins(
            'infrastructure').index('php_eggs'), 1)

        self.assertEqual(self.core.plugins.plugins[
                         'infrastructure'][0].get_name(), 'server_header')
        self.assertEqual(self.core.plugins.plugins[
                         'infrastructure'][1].get_name(), 'php_eggs')

    def test_enable_dependency_different_type(self):
        enabled_crawl = ['url_fuzzer', ]
        self.core.plugins.set_plugins(enabled_crawl, 'crawl')

        enabled_infra = ['allowed_methods', ]

        self.core.plugins.init_plugins()

        self.assertEquals(set(self.core.plugins.get_enabled_plugins('crawl')),
                          set(enabled_crawl))

        self.assertEquals(
            set(self.core.plugins.get_enabled_plugins('infrastructure')),
            set(enabled_infra))

    def test_enable_all_all(self):
        for plugin_type in self.core.plugins.get_plugin_types():
            self.core.plugins.set_plugins(['all', ], plugin_type)

        self.core.plugins.init_plugins()

        for plugin_type in self.core.plugins.get_plugin_types():
            enabled_plugins = self.core.plugins.get_enabled_plugins(
                plugin_type)
            all_plugins = self.core.plugins.get_plugin_list(plugin_type)
            self.assertEqual(set(enabled_plugins), set(all_plugins))
            self.assertEqual(len(enabled_plugins), len(all_plugins))


def listdir_remove_fs(query_dir):
    """
    Many builds, such as [0], fail because we're running multiple tests at the
    same time; and some of those tests write new/test plugins to disk. I've
    tried to modify those tests to avoid writing the file... but it was almost
    impossible and too hacky solution.

    This simple function replaces the "os.listdir" command, returning a list of
    the files in the the query_dir, removing 'failing_spider' plugin name from
    the list.

    [0] https://circleci.com/gh/andresriancho/w3af/801

    :param query_dir: The directory to query
    :return: A list without 'failing_spider'
    """
    original = orig_listdir(query_dir)
    result = []

    for fname in original:
        if TEST_PLUGIN_NAME not in fname:
            result.append(fname)

    return result