"""
test_deserialization.py

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
import re
import urllib
import cPickle
import base64

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


test_config = {
    'audit': (PluginConfig('deserialization'),),
}


class TestDeserializePickle(PluginTest):

    target_url = 'http://mock/deserialize?message='

    class DeserializeMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            b64message = uri[uri.find('=') + 1:]

            try:
                message = base64.b64decode(b64message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            try:
                cPickle.loads(message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            body = 'Message received'
            return self.status, response_headers, body

    MOCK_RESPONSES = [DeserializeMockResponse(re.compile('.*'), body=None,
                                              method='GET', status=200)]

    def test_found_deserialization_in_pickle(self):
        self._scan(self.target_url, test_config)
        vulns = self.kb.get('deserialization', 'deserialization')

        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]

        self.assertEquals('message', vuln.get_token_name())
        self.assertEquals('Insecure deserialization', vuln.get_name())
