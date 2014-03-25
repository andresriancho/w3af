"""
test_afd.py

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

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


BAD_SIG_URI = re.compile('.*(passwd|uname|passthru|xp_cmdshell|WINNT).*', re.I)


class TestFoundAFD(PluginTest):

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('afd'),)}
        }
    }


    MOCK_RESPONSES = [MockResponse('/', 'PASS'),
                      MockResponse(BAD_SIG_URI, 'FAIL')]

    def test_afd_found_http(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        infos = self.kb.get('afd', 'afd')

        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        self.assertEqual(info.get_name(), 'Active filter detected')
        values = [u.url_string.split('=')[1] for u in info['filtered']]

        self.assertIn('../../../../etc/passwd', set(values), values)


class TestFoundHttpsAFD(TestFoundAFD):
    target_url = 'https://httpretty/'


class TestNotFoundAFD(PluginTest):
    target_url = get_moth_http()

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('afd'),)}
        }
    }

    def test_afd_not_found_http(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        infos = self.kb.get('afd', 'afd')

        self.assertEqual(len(infos), 0, infos)
