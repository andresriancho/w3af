"""
test_ms15_034.py

Copyright 2015 Andres Riancho

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


class TestFindMS14_034(PluginTest):

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('ms15_034'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse(target_url, 'PASS', status=416)]

    def test_vulnerable_host(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        infos = self.kb.get('ms15_034', 'ms15_034')

        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        self.assertEqual(info.get_name(), 'MS15-034')


class TestNotFindMS14_034(PluginTest):

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('ms15_034'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse(target_url, 'PASS', status=415)]

    def test_vulnerable_host(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        infos = self.kb.get('ms15_034', 'ms15_034')
        self.assertEqual(len(infos), 0, infos)