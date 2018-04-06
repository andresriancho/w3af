"""
test_open_api.py

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
from w3af.core.data.dc.headers import Headers

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.data.parsers.doc.open_api.tests.example_specifications import (IntParamQueryString,
                                                                              NestedModel)


class TestOpenAPIFindAllEndpointsWithAuth(PluginTest):

    target_url = 'http://w3af.org/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('open_api',

                                               ('query_string_auth',
                                                'api_key=0x12345',
                                                PluginConfig.QUERY_STRING),

                                               ),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://w3af.org/swagger.json',
                                   IntParamQueryString().get_specification())]

    def test_find_all_endpoints_with_auth(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        #
        # Since we configured authentication we should only get one of the Info
        #
        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 1, infos)

        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')

        #
        # Now check that we found all the fuzzable requests
        #
        fuzzable_requests = self.kb.get_all_known_fuzzable_requests()

        self.assertEqual(len(fuzzable_requests), 4)

        # Remove the /swagger.json and /
        fuzzable_requests = [f for f in fuzzable_requests if f.get_url().get_path() not in ('/swagger.json', '/')]

        # Order them to be able to easily assert things
        def by_path(fra, frb):
            return cmp(fra.get_url().url_string, frb.get_url().url_string)

        fuzzable_requests.sort(by_path)

        #
        # Assertions on call #1
        #
        fuzzable_request = fuzzable_requests[0]

        e_url = 'http://w3af.org/api/pets?api_key=0x12345'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '')

        #
        # Assertions on call #2
        #
        fuzzable_request = fuzzable_requests[1]

        e_url = 'http://w3af.org/api/pets?limit=42&api_key=0x12345'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '')


class TestOpenAPINestedModelSpec(PluginTest):
    target_url = 'http://w3af.org/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('open_api',

                                               ('header_auth',
                                                'Basic: bearer 0x12345',
                                                PluginConfig.HEADER),

                                               ),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://w3af.org/openapi.json',
                                   NestedModel().get_specification())]

    def test_find_all_endpoints_with_auth(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        #
        # Since we configured authentication we should only get one of the Info
        #
        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 1, infos)

        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')

        #
        # Now check that we found all the fuzzable requests
        #
        fuzzable_requests = self.kb.get_all_known_fuzzable_requests()

        self.assertEqual(len(fuzzable_requests), 3)

        # Remove the /openapi.json and /
        fuzzable_requests = [f for f in fuzzable_requests if f.get_url().get_path() not in ('/openapi.json', '/')]

        # Order them to be able to easily assert things
        def by_path(fra, frb):
            return cmp(fra.get_url().url_string, frb.get_url().url_string)

        fuzzable_requests.sort(by_path)

        self.assertEqual(len(fuzzable_requests), 1)

        #
        # Assertions on call #1
        #
        fuzzable_request = fuzzable_requests[0]

        e_url = 'http://w3af.org/api/pets'
        e_data = '{"pet": {"tag": "7", "name": "John", "id": 42}}'
        e_headers = Headers([('Content-Type', 'application/json'),
                             ('Basic', 'bearer 0x12345')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)


class TestOpenAPIRaisesWarningIfNoAuth(PluginTest):
    target_url = 'http://w3af.org/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('open_api'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://w3af.org/openapi.json',
                                   NestedModel().get_specification())]

    def test_auth_warning_raised(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        #
        # Since we configured authentication we should only get one of the Info
        #
        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 2, infos)

        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')

        info_i = infos[1]
        self.assertEqual(info_i.get_name(), 'Open API missing credentials')


class TestOpenAPIFindsSpecInOtherDirectory(PluginTest):
    target_url = 'http://w3af.org/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('open_api'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://w3af.org/api/v2/openapi.json',
                                   NestedModel().get_specification())]

    def test_auth_warning_raised(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        #
        # Since we configured authentication we should only get one of the Info
        #
        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 2, infos)

        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')


class TestOpenAPIFindsSpecInOtherDirectory2(PluginTest):
    target_url = 'http://w3af.org/a/b/c/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('open_api'),)}
        }
    }

    MOCK_RESPONSES = [MockResponse('http://w3af.org/a/openapi.json',
                                   NestedModel().get_specification())]

    def test_auth_warning_raised(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        #
        # Since we configured authentication we should only get one of the Info
        #
        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 2, infos)

        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')

