"""
test_vulners_db.py

Copyright 2018 Andres Riancho

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


class TestVulnersDB(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='',
                                   method='GET',
                                   status=200,
                                   headers={'content-length': '0',
                                            'server': 'Microsoft-IIS/7.5',
                                            'x-aspnet-version': '2.0.50727',
                                            'x-powered-by': 'ASP.NET',
                                            'microsoftsharepointteamservices': '14.0.0.4762'}),
                      ]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('vulners_db'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_vulns_detected(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('vulners_db', 'HTML')

        self.assertEqual(len(vulns), 5, vulns)

        expected_names = {'CVE-2010-2730',
                          'CVE-2010-1256',
                          'CVE-2010-3972',
                          'CVE-2012-2531',
                          'CVE-2010-1899'}

        names = {i.get_name() for i in vulns}

        self.assertEqual(names, expected_names)

        vuln = [i for i in vulns if i.get_name() == 'CVE-2012-2531'][0]

        self.assertEqual(vuln.get_name(), 'CVE-2012-2531')
        self.assertEqual(vuln.get_url().url_string, 'http://httpretty/')

        expected_desc = (u'Vulners plugin detected software with known vulnerabilities.'
                         u' The identified vulnerability is "CVE-2012-2531".\n'
                         u'\n'
                         u' The first ten URLs where vulnerable software was detected are:\n'
                         u' - http://httpretty/\n')
        self.assertEqual(vuln.get_desc(with_id=False), expected_desc)

