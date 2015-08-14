"""
test_application_fingerprint.py

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


class TestApplicationFingerprint(PluginTest):
    target_url = 'http://application-fingerprint/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'infrastructure': (PluginConfig('application_fingerprint'),)
            }
        }
    }

    MOCK_RESPONSES = [
        MockResponse('http://application-fingerprint/jquery-in-content',
                     '<script src="jquery.js"></script>'),
        MockResponse('http://application-fingerprint/apache-without-content',
                     '', headers={'Server': 'Apache'}),
    ]

    def get_human_readable_info(self):
        infos = self.kb.get('application_fingerprint',
                            'Application fingerprint')

        self.assertEqual(len(infos), 1, infos)
        return infos[0]

    def get_raw_data(self, url):
        raw_dict = self.kb.raw_read('application_fingerprint',
                                    'application_fingerprint')

        self.assertEqual(len(raw_dict.keys()), 1, raw_dict.keys())
        self.assertIn(url, raw_dict)
        apps = [data_dict['app'] for data_dict in raw_dict[url]]
        return raw_dict, apps

    def test_apache(self):
        cfg = self._run_configs['cfg']
        url = self.target_url + 'apache-without-content'
        self._scan(url, cfg['plugins'])

        info = self.get_human_readable_info()

        self.assertIn('Apache', info.get_desc())
        self.assertNotIn('jQuery', info.get_desc())

        raw_dict, apps = self.get_raw_data(url)

        self.assertIn('Apache', apps)
        self.assertNotIn('jQuery', apps)

    def test_jquery(self):
        cfg = self._run_configs['cfg']
        url = self.target_url + 'jquery-in-content'
        self._scan(url, cfg['plugins'])

        info = self.get_human_readable_info()

        self.assertIn('jQuery', info.get_desc())
        self.assertNotIn('Apache', info.get_desc())

        raw_dict, apps = self.get_raw_data(url)

        self.assertIn('jQuery', apps)
        self.assertNotIn('Apache', apps)
