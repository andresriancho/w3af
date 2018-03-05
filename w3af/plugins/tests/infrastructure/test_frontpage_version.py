"""
test_frontpage_version.py

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


class TestFrontpageVersion(PluginTest):

    target_url = 'http://httpretty'

    FRONTPAGE_BODY = ('FPVersion="1.2.3"\n'
                      'FPAdminScriptUrl="/admin"\n'
                      'FPAuthorScriptUrl="/author"\n')

    MOCK_RESPONSES = [MockResponse('http://httpretty/_vti_inf.html',
                                   body=FRONTPAGE_BODY,
                                   method='GET', status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('frontpage_version'),)}
        }
    }

    def test_find_version(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('frontpage_version', 'frontpage_version')

        EXPECTED = ('/_vti_inf.html',
                    '/author',
                    '/admin')

        self.assertEqual(len(infos), len(EXPECTED), infos)

        self.assertEqual(set([self.target_url + path_file for path_file in EXPECTED]),
                         set([i.get_url().url_string for i in infos]))
