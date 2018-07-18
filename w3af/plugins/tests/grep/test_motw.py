"""
test_motw.py

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
import w3af.core.data.constants.severity as severity

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestValidMOTW(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='<!-- saved from url=(0011)http://a/ -->',
                                   method='GET',
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('motw'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        infos = self.kb.get('motw', 'motw')

        self.assertEquals(1, len(infos), infos)

        self.assertEquals(set([severity.INFORMATION] * 2),
                          set([v.get_severity() for v in infos]))

        self.assertEqual(v.get_name(), 'Mark of the web')


class TestInvalidMOTW(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body="<!-- saved from      url='http://a/' -->",
                                   method='GET',
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('motw'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        infos = self.kb.get('motw', 'motw')

        self.assertEquals(0, len(infos), infos)
