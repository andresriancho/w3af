"""
test_response_splitting.py

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

from nose.plugins.attrib import attr
from email.header import decode_header

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class ResponseSplittingMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        uri = urllib.unquote(uri)
        headers_to_inject = uri[uri.find('=') + 1:]
        header_name_1 = 'somevalue'

        try:
            headers_to_inject = headers_to_inject.split('\n')
            header_value_1 = headers_to_inject[0].strip()

            headers_to_inject = headers_to_inject[1]
            header_name_2, header_value_2 = headers_to_inject.split(':')
            header_name_2 = header_name_2.strip()
            header_value_2 = header_value_2.strip()
        except:
            return self.status, response_headers, self.body
        else:
            response_headers[header_name_1] = header_value_1
            response_headers[header_name_2] = header_value_2
            return self.status, response_headers, self.body


@attr('smoke')
class TestResponseSplitting(PluginTest):

    target_url = 'http://w3af.org/?header='
    target_url_re = re.compile('http://w3af\\.org/\\?header=.*')

    MOCK_RESPONSES = [ResponseSplittingMockResponse(target_url_re,
                                                    body='',
                                                    method='GET',
                                                    status=200)]
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('response_splitting'),),
            }
        },
    }

    def test_found_response_splitting(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('response_splitting', 'response_splitting')
        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Response splitting vulnerability', vuln.get_name())
        self.assertEquals('http://w3af.org/', str(vuln.get_url()))
        self.assertEquals('header', vuln.get_token_name())


class ResponseSplittingParameterModifiesResponseMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        uri = urllib.unquote(uri)
        headers_to_inject = uri[uri.find('=') + 1:]

        header_name_1 = 'somevalue'

        try:
            headers_to_inject = headers_to_inject.split('\n')
            header_value_1 = headers_to_inject[0].strip()

            headers_to_inject = headers_to_inject[1]
            header_name_2, header_value_2 = headers_to_inject.split(':')
            header_name_2 = header_name_2.strip()
            header_value_2 = header_value_2.strip()
        except:
            return self.status, response_headers, self.body
        else:
            response_headers[header_name_1] = header_value_1

            body = self.body
            if header_name_2 and header_value_2:
                body = 'Header may not contain more than a single header, new line detected'

            return self.status, response_headers, body


class TestResponseSplittingParameterModifiesResponse(PluginTest):
    target_url = 'http://w3af.org/?header='
    target_url_re = re.compile('http://w3af\\.org/\\?header=.*')

    MOCK_RESPONSES = [ResponseSplittingParameterModifiesResponseMockResponse(target_url_re,
                                                                             body='',
                                                                             method='GET',
                                                                             status=200)]
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('response_splitting'),),
            }
        },
    }

    def test_found_response_splitting_modifies_response(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('response_splitting', 'response_splitting')
        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Parameter modifies response headers', vuln.get_name())
        self.assertEquals('http://w3af.org/', str(vuln.get_url()))
        self.assertEquals('header', vuln.get_token_name())


class ResponseSplittingHeaderMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        referer = http_request.headers.get('Referer') or ''
        headers_to_inject = decode_header(referer)[0][0]

        header_name_1 = 'somevalue'

        try:
            headers_to_inject = headers_to_inject.split('\n')
            header_value_1 = headers_to_inject[0].strip()

            headers_to_inject = headers_to_inject[1]
            header_name_2, header_value_2 = headers_to_inject.split(':')
            header_name_2 = header_name_2.strip()
            header_value_2 = header_value_2.strip()
        except:
            return self.status, response_headers, self.body
        else:
            response_headers[header_name_1] = header_value_1
            response_headers[header_name_2] = header_value_2
            return self.status, response_headers, self.body


class TestResponseSplittingHeader(PluginTest):
    target_url = 'http://w3af.org/'
    target_url_re = re.compile('http://w3af\\.org/.*')

    MOCK_RESPONSES = [ResponseSplittingHeaderMockResponse(target_url_re,
                                                          body='',
                                                          method='GET',
                                                          status=200)]
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('response_splitting'),),
            },
            'misc_settings': {'fuzzable_headers': ['referer']}
        },
    }

    def test_response_splitting_headers(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'],
                   cfg['plugins'],
                   misc_settings=cfg['misc_settings'])

        vulns = self.kb.get('response_splitting', 'response_splitting')
        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Response splitting vulnerability', vuln.get_name())
        self.assertEquals('http://w3af.org/', str(vuln.get_url()))
        self.assertEquals('referer', vuln.get_token_name())
