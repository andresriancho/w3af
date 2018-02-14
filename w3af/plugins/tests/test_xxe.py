"""
test_xxe.py

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

from lxml import etree

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


test_config = {
    'audit': (PluginConfig('xxe'),),
}


class TestXXESimple(PluginTest):

    target_url = 'http://mock/xxe.simple?xml='

    class XXEMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            xml = uri[uri.find('=') + 1:]

            # A very vulnerable parser
            parser = etree.XMLParser(load_dtd=True,
                                     no_network=False,
                                     resolve_entities=True)
            try:
                root = etree.fromstring(str(xml), parser=parser)
                body = etree.tostring(root)
            except Exception, e:
                body = str(e)

            return self.status, response_headers, body

    MOCK_RESPONSES = [XXEMockResponse(re.compile('.*'), body=None,
                                      method='GET', status=200)]

    def test_found_xxe(self):
        self._scan(self.target_url, test_config)
        vulns = self.kb.get('xxe', 'xxe')

        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]

        self.assertEquals('xml', vuln.get_token_name())
        self.assertEquals('XML External Entity', vuln.get_name())


class TestXXENegativeWithError(PluginTest):

    target_url = 'http://mock/xxe.simple?xml='

    class XXEMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            xml = uri[uri.find('=') + 1:]

            # Secure
            parser = etree.XMLParser(load_dtd=False,
                                     no_network=True,
                                     resolve_entities=False)

            try:
                root = etree.fromstring(str(xml), parser=parser)
                body = etree.tostring(root)
            except Exception, e:
                body = str(e)

            return self.status, response_headers, body

    MOCK_RESPONSES = [XXEMockResponse(re.compile('.*'), body=None,
                                      method='GET', status=200)]

    def test_not_found_xxe(self):
        self._scan(self.target_url, test_config)
        errors = self.kb.get('xxe', 'errors')
        vulns = self.kb.get('xxe', 'xxe')

        self.assertEquals(0, len(vulns), vulns)
        self.assertEquals(1, len(errors), errors)

        # Now some tests around specific details of the found vuln
        error = errors[0]

        self.assertEquals('xml', error.get_token_name())
        self.assertEquals('XML Parsing Error', error.get_name())


class TestXXENegativeNoError(PluginTest):

    target_url = 'http://mock/xxe.simple?xml='

    class XXEMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            xml = uri[uri.find('=') + 1:]

            # Secure
            parser = etree.XMLParser(load_dtd=False,
                                     no_network=True,
                                     resolve_entities=False)

            try:
                root = etree.fromstring(str(xml), parser=parser)
                body = etree.tostring(root)
            except Exception, e:
                body = 'Generic error here'

            return self.status, response_headers, body

    MOCK_RESPONSES = [XXEMockResponse(re.compile('.*'), body=None,
                                      method='GET', status=200)]

    def test_not_found_xxe(self):
        self._scan(self.target_url, test_config)
        errors = self.kb.get('xxe', 'errors')
        vulns = self.kb.get('xxe', 'xxe')

        self.assertEquals(0, len(vulns), vulns)
        self.assertEquals(0, len(errors), errors)
