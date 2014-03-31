"""
test_user_dir.py

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
from mock import Mock

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestUserDir(PluginTest):

    target_url = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('user_dir'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('/~www/', 'www user home directory.')]

    def test_fuzzer_user(self):
        # Don't enable dependencies
        self.w3afcore.plugins.resolve_dependencies = Mock()

        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        users = self.kb.get('user_dir', 'users')

        self.assertEqual(len(users), 1, users)

        user = users[0]

        self.assertTrue(user.get_name().startswith('Web user home directory'))
        self.assertEquals(user.get_url().url_string, 'http://moth/~www/')