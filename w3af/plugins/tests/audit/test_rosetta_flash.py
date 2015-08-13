"""
test_rosetta_flash.py

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

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.data.parsers.doc.url import URL


CONFIG = {
    'audit': (PluginConfig('rosetta_flash'),),
}


class TestRosettaFlash(PluginTest):

    target_url = 'http://mock/jsonp?callback='

    class JSONPMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = URL(uri)

            try:
                callback = uri.get_querystring()['callback'][0]
            except KeyError:
                callback = 'default'

            body = '%s({})' % callback
            response_headers['Content-Type'] = 'application/javascript'

            return self.status, response_headers, body

    MOCK_RESPONSES = [JSONPMockResponse(re.compile('.*'), body=None,
                                        method='GET', status=200,
                                        content_type='application/javascript')]

    def test_found_rosetta_flash(self):
        self._scan(self.target_url, CONFIG)
        vulns = self.kb.get('rosetta_flash', 'rosetta_flash')

        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]

        self.assertEquals('callback', vuln.get_token_name())
        self.assertEquals('Rosetta Flash', vuln.get_name())
        self.assertEquals(URL(self.target_url).uri2url().url_string,
                          vuln.get_url().url_string)


class TestRosettaFlashFixed(PluginTest):

    target_url = 'http://mock/jsonp?callback='

    class JSONPMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = URL(uri)

            try:
                callback = uri.get_querystring()['callback'][0]
            except KeyError:
                callback = 'default'

            #
            # Here is the fix! Note the /**/
            #
            body = '/**/%s({})' % callback
            response_headers['Content-Type'] = 'application/javascript'

            return self.status, response_headers, body

    MOCK_RESPONSES = [JSONPMockResponse(re.compile('.*'), body=None,
                                        method='GET', status=200,
                                        content_type='application/javascript')]

    def test_not_found_rosetta_flash(self):
        self._scan(self.target_url, CONFIG)
        vulns = self.kb.get('rosetta_flash', 'rosetta_flash')

        self.assertEquals(0, len(vulns), vulns)