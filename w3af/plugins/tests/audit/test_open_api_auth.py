"""
test_open_api_auth.py

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
import os
import re

from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.open_api import OpenAPI

from w3af.core.data.parsers.doc.open_api.specification import SpecificationHandler
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.plugins.audit.open_api_auth import open_api_auth
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


CURRENT_PATH = os.path.split(__file__)[0]


def by_path(fra, frb):
    return cmp(fra.get_url().url_string, frb.get_url().url_string)


def generate_response(specification_as_string):
    url = URL('http://www.w3af.com/openapi.yaml')
    headers = Headers([('content-type', 'application/yaml')])
    return HTTPResponse(200, specification_as_string, headers,
                        url, url, _id=1)


class PetstoreWithSecurity(object):

    @staticmethod
    def get_specification():
        return file('%s/data/petstore_with_security.yaml' % CURRENT_PATH).read()


class TestOpenAPIAuthWithPetstore(PluginTest):

    target_url = 'http://w3af.org/'
    api_key_auth = ('header_auth', 'X-API-Key: xxx', PluginConfig.HEADER)

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'crawl': (PluginConfig('open_api', api_key_auth,),),
                'audit': (PluginConfig('open_api_auth'),)
            }
        }
    }

    class AuthMockResponse(MockResponse):

        def get_response(self, http_request, uri, response_headers):
            if http_request.headers.get('X-API-Key', '') != 'xxx':
                return 401, response_headers, ''

            return self.status, response_headers, '{ "id": 42 }'

    MOCK_RESPONSES = [

        # No auth required for the API spec.
        MockResponse('http://w3af.org/openapi.yaml',
                     PetstoreWithSecurity().get_specification(),
                     content_type='application/yaml'),

        # No auth required for the health check endpoint.
        MockResponse('http://w3af.org/api/ping',
                     '',
                     content_type='text/plain'),

        # Authenticate GET requests to /api/pets
        AuthMockResponse(re.compile('http://w3af.org/api/pets$'),
                         '{ "id": 42 }',
                         content_type='application/json',
                         method='GET'),

        # No auth for POST requests to /api/pets
        # This should result to a vulnerability.
        MockResponse(re.compile('http://w3af.org/api/pets$'),
                     '{ "id": 42 }',
                     content_type='application/json',
                     method='POST'),

        # Authenticate requests to /api/pets/{id}
        AuthMockResponse(re.compile('http://w3af.org/api/pets.*'),
                         '{ "id": 42 }',
                         content_type='application/json')
    ]

    def test_petstore_with_security(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        specification_handler = self.kb.raw_read('open_api',
                                                 'specification_handler')
        self.assertIsNotNone(specification_handler, "no specification handler")
        self.assertTrue(isinstance(specification_handler, SpecificationHandler),
                        "not a SpecificationHandler")

        infos = self.kb.get('open_api', 'open_api')
        self.assertEqual(len(infos), 1, infos)
        info_i = infos[0]
        self.assertEqual(info_i.get_name(), 'Open API specification found')

        frs = self.kb.get_all_known_fuzzable_requests()
        frs = [f for f in frs if f.get_url().get_path() not in ('/openapi.yaml', '/')]
        frs.sort(by_path)
        self.assertEqual(len(frs), 6)

        vulns = self.kb.get('open_api_auth', 'open_api_auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals('Broken authentication', vuln.get_name())
        self.assertEquals('High', vuln.get_severity())
        self.assertEquals('http://w3af.org/api/pets', vuln.get_url().url_string)
        self.assertEquals('POST', vuln['method'])
        self.assertEquals(200, vuln['response_code'])


class TestOpenAPIAuth(PluginTest):

    def init_plugin(self):
        api_http_response = generate_response(PetstoreWithSecurity.get_specification())
        parser = OpenAPI(api_http_response)
        parser.parse()
        self.kb.raw_write('open_api', 'specification_handler',
                          parser.get_specification_handler().shallow_copy())
        self.kb.raw_write('open_api', 'request_to_operation_id',
                          parser.get_request_to_operation_id())

        spec = parser.get_specification_handler().get_spec()

        plugin = open_api_auth()
        self.assertTrue(plugin._is_api_spec_available())
        self.assertTrue(plugin._has_security_definitions_in_spec())

        return plugin, spec

    def test_with_bearer(self):
        plugin, spec = self.init_plugin()

        fr = FuzzableRequest(URL('http://w3af.org/api/pets'),
                             headers=Headers([('Authorization', 'Bearer xxx')]),
                             post_data=KeyValueContainer(),
                             method='GET')

        self.assertTrue(plugin._is_acceptable_auth_type(fr, 'oauth2'))
        self.assertTrue(plugin._is_acceptable_auth_type(fr, 'apiKey'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'basic'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'unknown'))

        self.assertTrue(plugin._has_auth(fr))
        self.assertTrue(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_basic_auth(fr))

        # Remove auth info from the request.
        updated_fr = plugin._remove_auth(fr)

        # Make sure that the original request still has auth info.
        self.assertTrue(plugin._has_auth(fr))
        self.assertTrue(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_basic_auth(fr))

        # Check if the updated request doesn't have auth info.
        self.assertFalse(plugin._has_auth(updated_fr))
        self.assertFalse(plugin._has_api_key(updated_fr,
                                             spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(updated_fr))
        self.assertFalse(plugin._has_basic_auth(updated_fr))

    def test_with_api_key(self):
        plugin, spec = self.init_plugin()

        fr = FuzzableRequest(URL('http://w3af.org/api/pets'),
                             headers=Headers([('X-API-Key', 'zzz')]),
                             post_data=KeyValueContainer(),
                             method='POST')

        self.assertTrue(plugin._is_acceptable_auth_type(fr, 'oauth2'))
        self.assertTrue(plugin._is_acceptable_auth_type(fr, 'apiKey'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'basic'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'unknown'))

        self.assertTrue(plugin._has_auth(fr))
        self.assertTrue(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_basic_auth(fr))

        # Remove auth info from the request.
        updated_fr = plugin._remove_auth(fr)

        # Make sure that the original request still has auth info.
        self.assertTrue(plugin._has_auth(fr))
        self.assertTrue(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_basic_auth(fr))

        # Check if the updated request doesn't have auth info.
        self.assertFalse(plugin._has_auth(updated_fr))
        self.assertFalse(plugin._has_api_key(updated_fr,
                                             spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(updated_fr))
        self.assertFalse(plugin._has_basic_auth(updated_fr))

    def test_with_no_auth(self):
        plugin, spec = self.init_plugin()

        fr = FuzzableRequest(URL('http://w3af.org/api/pets'),
                             headers=Headers([('X-Foo-Header', 'foo'), ('X-Bar-Header', 'bar')]),
                             post_data=KeyValueContainer(),
                             method='PUT')
        self.assertFalse(plugin._has_auth(fr))
        self.assertFalse(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_basic_auth(fr))

        # Remove auth info from the request.
        updated_fr = plugin._remove_auth(fr)

        self.assertFalse(plugin._has_auth(updated_fr))
        self.assertFalse(plugin._has_api_key(updated_fr,
                                             spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_oauth2(updated_fr))
        self.assertFalse(plugin._has_basic_auth(updated_fr))

        open_api_auth._remove_header(fr, 'X-Bar-Header')
        self.assertFalse(fr.get_headers().icontains('X-Bar-Header'))
        self.assertTrue(fr.get_headers().icontains('X-Foo-Header'))

    def test_no_security(self):
        plugin, spec = self.init_plugin()

        # Check the endpoint which doesn't require auth.
        fr = FuzzableRequest(URL('http://w3af.org/api/ping'),
                             headers=Headers(),
                             post_data=KeyValueContainer(),
                             method='GET')

        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'oauth2'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'apiKey'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'basic'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'unknown'))
        self.assertFalse(plugin._has_auth(fr))
        self.assertFalse(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_basic_auth(fr))

    def test_with_global_security(self):
        plugin, spec = self.init_plugin()

        # /api/pets/{id} doesn't have a 'security' section
        # but global 'security' section should apply here (only OAuth2)
        fr = FuzzableRequest(URL('http://w3af.org/api/pets/42'),
                             headers=Headers([('Authorization', 'Bearer xxx')]),
                             post_data=KeyValueContainer(),
                             method='GET')

        self.assertTrue(plugin._is_acceptable_auth_type(fr, 'oauth2'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'apiKey'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'basic'))
        self.assertFalse(plugin._is_acceptable_auth_type(fr, 'unknown'))

        self.assertTrue(plugin._has_auth(fr))
        self.assertTrue(plugin._has_oauth2(fr))
        self.assertFalse(plugin._has_api_key(fr, spec.security_definitions['ApiKeyAuth']))
        self.assertFalse(plugin._has_basic_auth(fr))
