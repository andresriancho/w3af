"""
test_buffer_overflow.py

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

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestBufferOverflow(PluginTest):

    target_url = 'http://mock/bo.c'

    class BOMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            if len(uri) > 800:
                body = '"*** stack smashing detected ***:"'
            else:
                body = 'A regular body without errors'

            return self.status, response_headers, body

    MOCK_RESPONSES = [BOMockResponse(re.compile('.*'), body=None,
                                     method='GET', status=200)]

    _run_config = {
        'target': target_url + '?buf=',
        'plugins': {
            'audit': (PluginConfig('buffer_overflow',),),
        }
    }

    def test_found_bo(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('buffer_overflow', 'buffer_overflow')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Buffer overflow vulnerability', vuln.get_name())
        self.assertEquals('buf', vuln.get_token_name())
        self.assertEquals(self.target_url, str(vuln.get_url()))


