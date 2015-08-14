"""
test_fingerprint_waf.py

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


class WAFTest(object):
    domain = 'httpretty-mock'
    target_url = 'http://%s/' % domain

    _run_configs = {
        'cfg': {
        'target': target_url,
        'plugins': {'infrastructure': (PluginConfig('fingerprint_WAF'),)}
        }
    }


class TestFingerprintWAFIBMWebSphere(WAFTest, PluginTest):

    IBM_WAF = 'X-Backside-Transport=1'
    MOCK_RESPONSES = [MockResponse(WAFTest.target_url, 'Hello world',
                                   headers={'Set-Cookie': IBM_WAF})]

    def test_fingerprint_waf(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('fingerprint_WAF', 'IBM WebSphere')
        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        name = 'Web Application Firewall fingerprint'
        desc = 'The remote network seems to have a "IBM WebSphere" WAF' \
               ' deployed to protect access to the web server. The following' \
               ' is the WAF\'s version: "X-Backside-Transport=1".'

        self.assertEqual(info.get_name(), name)
        self.assertEqual(info.get_desc(with_id=False), desc)
        self.assertIn(self.IBM_WAF, info.get_desc())


class TestFingerprintWAFNone(WAFTest, PluginTest):

    MOCK_RESPONSES = [MockResponse(WAFTest.target_url, 'Hello world')]

    def test_fingerprint_waf(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('fingerprint_WAF', 'fingerprint_WAF')
        self.assertEqual(len(infos), 0, infos)
