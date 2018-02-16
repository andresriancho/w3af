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
from xml import sax

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from mock import patch


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


class NoOpContentHandler(sax.ContentHandler):
    def __init__(self):
        sax.ContentHandler.__init__(self)
        self.chars = ''

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass

    def characters(self, content):
        self.chars += content


class TestXXERemoteLoading(PluginTest):

    target_url = 'http://mock/xxe.simple?xml='

    class XXEMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            xml = uri[uri.find('=') + 1:]

            # A very vulnerable parser that loads remote files over https
            handler = NoOpContentHandler()

            try:
                sax.parseString(xml, handler)
            except Exception, e:
                body = str(e)
            else:
                body = handler.chars

            return self.status, response_headers, body

    MOCK_RESPONSES = [XXEMockResponse(re.compile('.*'), body=None,
                                      method='GET', status=200)]

    def test_found_xxe_with_remote(self):

        # Use this mock to make sure that the vulnerability is found using
        # remote loading
        with patch('w3af.plugins.audit.xxe.xxe.LINUX_FILES') as linux_mock:
            linux_mock.return_value = []
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


class TestXXEInParameter(PluginTest):

    XML_NOTE = ('<note>'
                '<to>Tove</to>'
                '<from>Jani</from>'
                '<heading>Reminder</heading>'
                '<body>Forget me this weekend!</body>'
                '</note>')

    target_url = 'http://mock/xxe.simple?xml=%s' % XML_NOTE

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
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            for tag in root.iter():
                if tag.tag == 'from':
                    return self.status, response_headers, tag.text

            return self.status, response_headers, 'Invalid XML.'

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
