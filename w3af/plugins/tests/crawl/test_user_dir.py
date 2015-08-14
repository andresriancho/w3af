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

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('user_dir'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://httpretty/~www/',
                                   'www user home directory.'),
                      MockResponse('http://httpretty/~kmem/',
                                   'kmem user home directory.'),
                      MockResponse('http://httpretty//xfs/',
                                   'home sweet home')]

    EXPECTED_RESULTS = {('Web user home directory', 'http://httpretty/~www/'),
                        ('Web user home directory', 'http://httpretty/~kmem/'),
                        ('Web user home directory', 'http://httpretty/xfs/'),
                        ('Identified installed application', 'http://httpretty/xfs/'),
                        ('Fingerprinted operating system', 'http://httpretty/~kmem/')}

    def test_fuzzer_user(self):
        # Don't enable dependencies
        self.w3afcore.plugins.resolve_dependencies = Mock()

        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        users = self.kb.get('user_dir', 'users')
        scan_results = set([(i.get_name(), i.get_url().url_string) for i in users])

        self.assertEqual(self.EXPECTED_RESULTS, scan_results)
