"""
test_jetleak.py

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
import re

from mock import patch
from httpretty.http import STATUSES
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestJetLeak(PluginTest):

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('jetleak'),)}
        }
    }

    JETLEAK_ERROR = 'Illegal character 0x0 in state'

    class JettyMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            referer = http_request.headers.getrawheader('Referer')

            if referer is not None and '\x00' in referer:
                body = 'See HTTP reason text'
                status = 400
            else:
                body = 'Regular response'
                status = 200

            return status, response_headers, body

    MOCK_RESPONSES = [JettyMockResponse(re.compile('.*'), body=None,
                                        method='GET', status=200)]

    def test_vulnerable_jetty(self):
        cfg = self._run_configs['cfg']

        with patch.dict(STATUSES, {400: self.JETLEAK_ERROR}):
            self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('jetleak', 'jetleak')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(), 'JetLeak')


class TestNoJetLeak(PluginTest):

    target_url = 'http://httpretty/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('jetleak'),)}
        }
    }

    class FixedJettyMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            body = 'Regular response'
            status = 200

            return status, response_headers, body

    MOCK_RESPONSES = [FixedJettyMockResponse(re.compile('.*'), body=None,
                                             method='GET', status=200)]

    def test_fixed_jetty(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('jetleak', 'jetleak')

        self.assertEqual(len(vulns), 0, vulns)
