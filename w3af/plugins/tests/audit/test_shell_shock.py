"""
test_shell_shock.py

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

RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('shell_shock'),),
            'crawl': (
                PluginConfig(
                    'web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
            )
        }
    }
}


class BasicShellShockTest(PluginTest):

    target_url = 'http://shell.com/cgi.bin'

    MOCK_RESPONSES = [MockResponse(url='http://shell.com/cgi.bin',
                                   body='foo bar',
                                   method='GET',
                                   status=200,
                                   headers={'shellshock': 'check'})]

    def test_shell_shock_basic(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('shell_shock', 'shell_shock')
        self.assertEquals(1, len(vulns))


class BasicNegativeShellShockTest(PluginTest):

    target_url = 'http://shell.com/cgi.bin'

    # No headers are returned here
    MOCK_RESPONSES = [MockResponse(url='http://shell.com/cgi.bin',
                                   body='foo bar',
                                   method='GET',
                                   status=200)]

    def test_shell_shock_basic(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('shell_shock', 'shell_shock')
        self.assertEquals(0, len(vulns))
