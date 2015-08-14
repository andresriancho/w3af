"""
test_server_status.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestServerStatus(PluginTest):

    target_url = 'http://httpretty-mock/'

    MOCK_RESPONSES = [MockResponse('http://httpretty-mock/server-status',
                                   '<dl><dt>Server Version: Apache/2.2.9 (Unix)</dt>'),]

    _run_configs = {
        'cfg': {
        'target': target_url,
        'plugins': {'infrastructure': (PluginConfig('server_status'),)}
        }
    }

    def test_find_server(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        server = self.kb.get('server_status', 'server')

        self.assertEqual(len(server), 1, server)
        self.assertTrue(
            'remote server version: "Apache/2.' in server[0].get_desc(),
            server[0].get_desc())