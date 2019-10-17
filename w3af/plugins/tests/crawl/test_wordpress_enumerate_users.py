# coding: utf8
"""
test_wordpress_enumerate_users.py

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
import re

from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestWordpressEnumerateUsers(PluginTest):

    wordpress_url = 'http://wordpress/'

    _run_configs = {
        'direct': {
            'target': wordpress_url,
            'plugins': {
                'crawl': (PluginConfig('wordpress_enumerate_users',),)
            },
        },
    }

    @attr('ci_fails')
    def test_enumerate_users(self):
        cfg = self._run_configs['direct']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('wordpress_enumerate_users', 'users')

        EXPECTED = set(['admin', 'andres'])

        self.assertEqual(len(infos), len(EXPECTED), infos)

        user_re = re.compile('WordPress user "(.*?)" found')
        enum_users = set([user_re.match(i.get_desc()).group(1) for i in infos])

        self.assertEquals(enum_users, EXPECTED)
