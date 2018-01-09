"""
test_frontpage.py

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
from mock import patch

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestFrontpage(PluginTest):

    target_url = 'http://httpretty'

    FRONTPAGE_BODY = ('FPVersion="1.2.3"\n'
                      'FPAdminScriptUrl="/admin"\n'
                      'FPAuthorScriptUrl="/author"\n')

    MOCK_RESPONSES = [MockResponse('http://httpretty/_vti_inf.html',
                                   body=FRONTPAGE_BODY,
                                   method='GET', status=200),
                      MockResponse('http://httpretty/author',
                                   body='',
                                   method='POST', status=200),
                      MockResponse('http://httpretty/AAAAAA.html',
                                   body='AAAAAA.html'[::-1],
                                   method='GET', status=200),
                      ]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('frontpage_version'),),
                        'audit': (PluginConfig('frontpage'),)}
        }
    }

    def test_upload(self):
        cfg = self._run_configs['cfg']

        with patch('w3af.plugins.audit.frontpage.rand_alpha') as rand_alpha_mock:
            rand_alpha_mock.side_effect = ['AAAAAA']
            self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('frontpage', 'frontpage')

        self.assertEqual(len(vulns), 1, vulns)

        vuln = vulns[0]

        self.assertEqual(vuln.get_url().url_string, 'http://httpretty/AAAAAA.html')
        self.assertEqual(vuln.get_name(), 'Insecure Frontpage extensions configuration')
