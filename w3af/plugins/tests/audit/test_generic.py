"""
test_generic.py

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
import urllib

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.audit.sqli import sqli


class TestGenericOnly(PluginTest):

    target_url = 'http://mock/?id='

    class GenericErrorMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)

            if uri.endswith('1/0'):
                body = 'Error found!'
            else:
                body = 'Sunny outside'

            return self.status, response_headers, body

    CONFIG = {'audit': (PluginConfig('generic'),)}
    MOCK_RESPONSES = [GenericErrorMockResponse(re.compile('.*'), body=None,
                                               method='GET', status=200)]

    def test_found_generic(self):
        self._scan(self.target_url, self.CONFIG)
        
        vulns = self.kb.get('generic', 'generic')
        
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Unhandled error in web application', vuln.get_name())
        self.assertEquals('http://mock/?id=1/0', str(vuln.get_uri()))
        self.assertEquals(vuln.get_mutant().get_token_name(), 'id')


class TestGenericExtensive(PluginTest):

    target_url = 'http://mock/?id='

    class GenericErrorMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)

            if uri.endswith('Infinity'):
                body = 'Error found!'
            else:
                body = 'Sunny outside'

            return self.status, response_headers, body

    CONFIG = {'audit': (PluginConfig('generic',
                                     ('extensive', True, PluginConfig.BOOL),),)}
    MOCK_RESPONSES = [GenericErrorMockResponse(re.compile('.*'), body=None,
                                               method='GET', status=200)]

    def test_found_generic_extensive(self):
        self._scan(self.target_url, self.CONFIG)

        vulns = self.kb.get('generic', 'generic')

        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Unhandled error in web application', vuln.get_name())
        self.assertEquals('http://mock/?id=Infinity', str(vuln.get_uri()))
        self.assertEquals(vuln.get_mutant().get_token_name(), 'id')


class TestGenericSQLInjection(PluginTest):

    target_url = 'http://mock/?id='

    class SQLIMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)

            if uri.endswith('1/0') or uri.endswith(sqli.SQLI_STRINGS[0]):
                body = 'PostgreSQL query failed:'
            else:
                body = 'Sunny outside'

            return self.status, response_headers, body

    CONFIG = {'audit': (PluginConfig('generic'),
                        PluginConfig('sqli'))}
    MOCK_RESPONSES = [SQLIMockResponse(re.compile('.*'), body=None,
                                       method='GET', status=200)]

    def test_found_sqli_not_generic(self):
        self._scan(self.target_url, self.CONFIG)

        vulns = self.kb.get('generic', 'generic')
        self.assertEquals(0, len(vulns))

        vulns = self.kb.get('sqli', 'sqli')
        self.assertEquals(1, len(vulns))
