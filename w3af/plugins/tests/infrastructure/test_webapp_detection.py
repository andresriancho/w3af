"""
test_webapp_detection.py

Copyright 2015 Piotr Lizonczyk

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


class TestWebappDetection(PluginTest):
    target_url = 'http://webapp-detection/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('webapp_detection'),)}
        }
    }

    MOCK_RESPONSES = [
        MockResponse('http://webapp-detection/jquery-in-content', '<script src="jquery.js"></script>'),
        MockResponse('http://webapp-detection/apache-in-headers-no-content', '', headers={'Server': 'Apache'}),
    ]

    def test_apache(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url + 'apache-in-headers-no-content', cfg['plugins'])

        infos = self.kb.get('webapp_detection', 'webapp_detection')

        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        self.assertIn('Apache', info.get_desc())

    def test_jquery(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url + 'jquery-in-content', cfg['plugins'])

        infos = self.kb.get('webapp_detection', 'webapp_detection')

        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        self.assertIn('jQuery', info.get_desc())
