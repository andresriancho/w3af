# -*- coding: UTF-8 -*-
"""
test_main.py

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
import unittest

from w3af import ROOT_PATH
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.open_api import OpenAPI
from w3af.core.data.url.HTTPResponse import HTTPResponse


# Order them to be able to easily assert things
def by_path(fra, frb):
    return cmp(fra.get_url().url_string, frb.get_url().url_string)


class TestOpenAPIMain(unittest.TestCase):
    DATA_PATH = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc', 'open_api', 'tests', 'data')

    SWAGGER_JSON = os.path.join(DATA_PATH, 'swagger.json')
    PETSTORE_SIMPLE = os.path.join(DATA_PATH, 'petstore-simple.json')
    PETSTORE_EXPANDED = os.path.join(DATA_PATH, 'petstore-simple.json')
    MULTIPLE_PATHS_AND_HEADERS = os.path.join(DATA_PATH, 'multiple_paths_and_headers.json')
    NOT_VALID_SPEC = os.path.join(DATA_PATH, 'not_quite_valid_petstore_simple.json')
    CUSTOM_CONTENT_TYPE = os.path.join(DATA_PATH, 'custom_content_type.json')
    UNKNOWN_CONTENT_TYPE = os.path.join(DATA_PATH, 'unknown_content_type.json')
    LARGE_MANY_ENDPOINTS = os.path.join(DATA_PATH, 'large_many_endpoints.json')
    MISSING_LICENSE = os.path.join(DATA_PATH, 'missing_license.json')
    REAL_API_YAML = os.path.join(DATA_PATH, 'real.yaml')
    ISSUE_210_API_YAML = os.path.join(DATA_PATH, '210-openapi.yaml')

    def test_json_pet_store(self):
        # http://petstore.swagger.io/v2/swagger.json
        body = file(self.SWAGGER_JSON).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        json_headers = Headers([('Content-Type', 'application/json')])
        multipart_headers = Headers([('Content-Type', 'multipart/form-data')])
        url_encoded_headers = Headers([('Content-Type', 'application/x-www-form-urlencoded')])
        json_api_headers = Headers([('api_key', 'FrAmE30.'),
                                    ('Content-Type', 'application/json')])

        url_root = 'http://petstore.swagger.io/v2'

        expected_body_1 = ('{"body": {"category": {"id": 42, "name": "John"},'
                           ' "status": "available", "name": "doggie",'
                           ' "tags": [{"id": 42, "name": "John"}],'
                           ' "photoUrls": ["56"], "id": 42}}')

        expected_body_2 = ('{"body": {"username": "John8212", "firstName": "John",'
                           ' "lastName": "Smith", "userStatus": 42,'
                           ' "email": "w3af@email.com", "phone": "55550178",'
                           ' "password": "FrAmE30.", "id": 42}}')

        expected_body_3 = ('{"body": [{"username": "John8212", "firstName": "John",'
                           ' "lastName": "Smith", "userStatus": 42,'
                           ' "email": "w3af@email.com", "phone": "55550178",'
                           ' "password": "FrAmE30.", "id": 42}]}')

        expected_body_4 = ('{"body": {"status": "placed",'
                           ' "shipDate": "2017-06-30T23:59:45",'
                           ' "complete": false, "petId": 42, "id": 42, "quantity": 42}}')

        e_api_calls = [
            ('GET', '/pet/findByStatus?status=available', json_headers, ''),
            ('POST', '/pet/42/uploadImage', multipart_headers, ''),
            ('POST', '/pet/42', url_encoded_headers, ''),
            ('POST', '/pet', json_headers, expected_body_1),
            ('GET', '/pet/42', json_headers, ''),
            ('GET', '/pet/42', json_api_headers, ''),
            ('GET', '/pet/findByTags?tags=56', json_headers, ''),
            ('PUT', '/pet', json_headers, expected_body_1),
            ('PUT', '/user/John8212', json_headers, expected_body_2),
            ('POST', '/user/createWithList', json_headers, expected_body_3),
            ('POST', '/user', json_headers, expected_body_2),
            ('GET', '/user/John8212', json_headers, ''),
            ('GET', '/user/login?username=John8212&password=FrAmE30.', json_headers, ''),
            ('GET', '/user/logout', Headers(), ''),
            ('POST', '/user/createWithArray', json_headers, expected_body_3),
            ('GET', '/store/order/2', json_headers, ''),
            ('GET', '/store/inventory', json_headers, ''),
            ('GET', '/store/inventory', json_api_headers, ''),
            ('POST', '/store/order', json_headers, expected_body_4),
        ]

        self.assertEqual(21, len(api_calls))

        for api_call in api_calls:
            method = api_call.get_method()
            headers = api_call.get_headers()
            data = api_call.get_data()

            uri = api_call.get_uri().url_string
            uri = uri.replace(url_root, '')

            data = (method, uri, headers, data)

            self.assertIn(data, e_api_calls)

    def test_json_multiple_paths_and_headers(self):
        body = file(self.MULTIPLE_PATHS_AND_HEADERS).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        api_calls.sort(by_path)

        self.assertEqual(len(api_calls), 4)

        #
        # Assertions on call #1
        #
        api_call = api_calls[0]

        e_url = 'http://w3af.org/api/cats'
        e_force_fuzzing_headers = ['X-Awesome-Header', 'X-Foo-Header']
        e_headers = Headers([
            ('X-Awesome-Header', '2018'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #2
        #
        api_call = api_calls[1]

        e_url = 'http://w3af.org/api/cats?limit=42'
        e_force_fuzzing_headers = ['X-Awesome-Header', 'X-Foo-Header']
        e_headers = Headers([
            ('X-Awesome-Header', '2018'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #3
        #
        api_call = api_calls[2]

        e_url = 'http://w3af.org/api/pets'
        e_force_fuzzing_headers = ['X-Bar-Header', 'X-Foo-Header']
        e_headers = Headers([
            ('X-Foo-Header', '42'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #4
        #
        api_call = api_calls[3]

        e_url = 'http://w3af.org/api/pets'
        e_force_fuzzing_headers = ['X-Bar-Header', 'X-Foo-Header']
        e_headers = Headers([
            ('X-Bar-Header', '56'),
            ('X-Foo-Header', '42'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

    # Check if the OpenAPI plugin takes into account content types provided in a 'consumes' list.
    def test_custom_content_type(self):
        body = file(self.CUSTOM_CONTENT_TYPE).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        api_calls.sort(by_path)

        self.assertEqual(len(api_calls), 2)

        #
        # Assertions on call #1
        #
        api_call = api_calls[0]

        e_url = 'http://w3af.org/api/pets'
        e_force_fuzzing_headers = []
        e_headers = Headers([('Content-Type', 'application/vnd.w3af+json')])
        e_post_data_headers = Headers([('Content-Type', 'application/vnd.w3af+json')])
        e_all_headers = Headers([('Content-Type', 'application/vnd.w3af+json')])

        self.assertIsInstance(api_call.get_raw_data(), JSONContainer)
        self.assertEquals(api_call.get_method(), 'PUT')
        self.assertEquals(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEquals(api_call.get_post_data_headers(), e_post_data_headers)
        self.assertEquals(api_call.get_all_headers(), e_all_headers)
        self.assertEquals(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)
        self.assertEquals(str(api_call.get_raw_data()), '{"info": {"tag": "7", "name": "John", "id": 42}}')

        #
        # Assertions on call #2
        #
        api_call = api_calls[1]

        e_url = 'http://w3af.org/api/pets'
        e_force_fuzzing_headers = ['X-Foo-Header']
        e_headers = Headers([('Content-Type', 'application/vnd.w3af+json'), ('X-Foo-Header', '42')])
        e_post_data_headers = Headers([('Content-Type', 'application/vnd.w3af+json')])
        e_all_headers = Headers([('Content-Type', 'application/vnd.w3af+json'), ('X-Foo-Header', '42')])

        self.assertIsInstance(api_call.get_raw_data(), JSONContainer)
        self.assertEquals(api_call.get_method(), 'POST')
        self.assertEquals(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEquals(api_call.get_post_data_headers(), e_post_data_headers)
        self.assertEquals(api_call.get_all_headers(), e_all_headers)
        self.assertEquals(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)
        self.assertEquals(str(api_call.get_raw_data()), '{"info": {"tag": "7", "name": "John"}}')

    # Check if the OpenAPI plugin doesn't return a fuzzable request for a endpoint
    # which contains an unknown content type in its 'consumes' list.
    def test_unknown_content_type(self):
        body = file(self.UNKNOWN_CONTENT_TYPE).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()
        self.assertEquals(api_calls, [])

    # Check if the OpenAPI parser can extract all api calls from a rather
    # large swagger file
    def test_large_many_endpoints(self):
        body = file(self.LARGE_MANY_ENDPOINTS).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        #
        # In some cases with validation enabled (not the default) we find a set
        # of endpoints:
        #
        parser = OpenAPI(response, validate_swagger_spec=True)
        parser.parse()
        api_calls = parser.get_api_calls()

        expected_api_calls = 161
        self.assertEqual(expected_api_calls, len(api_calls))

        #
        # And without spec validation there is a different set of endpoints:
        #
        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        expected_api_calls = 165
        self.assertEqual(expected_api_calls, len(api_calls))

        first_api_call = api_calls[0]
        uri = first_api_call.get_uri().url_string

        expected_uri = 'https://target.com/api/Partners/3419/Agreement?performedBy=56'

        self.assertEqual(expected_uri, uri)

    def test_disabling_headers_discovery(self):
        body = file(self.MULTIPLE_PATHS_AND_HEADERS).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response, discover_fuzzable_headers=False)
        parser.parse()
        api_calls = parser.get_api_calls()

        api_calls.sort(by_path)

        self.assertEqual(len(api_calls), 4)

        e_force_fuzzing_headers = []

        #
        # Assertions on call #1
        #
        api_call = api_calls[0]

        e_url = 'http://w3af.org/api/cats'
        e_headers = Headers([
            ('X-Awesome-Header', '2018'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #2
        #
        api_call = api_calls[1]

        e_url = 'http://w3af.org/api/cats?limit=42'
        e_headers = Headers([
            ('X-Awesome-Header', '2018'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #3
        #
        api_call = api_calls[2]

        e_url = 'http://w3af.org/api/pets'
        e_headers = Headers([
            ('X-Foo-Header', '42'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

        #
        # Assertions on call #4
        #
        api_call = api_calls[3]

        e_url = 'http://w3af.org/api/pets'
        e_headers = Headers([
            ('X-Bar-Header', '56'),
            ('X-Foo-Header', '42'),
            ('Content-Type', 'application/json')])

        self.assertEqual(api_call.get_method(), 'GET')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)

    def test_disabling_spec_validation(self):
        body = file(self.NOT_VALID_SPEC).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        #
        # By default we don't validate the swagger spec, which allows us to
        # parse some invalid specs and extract information
        #
        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()
        self.assertEqual(len(api_calls), 1)

        api_call = api_calls[0]
        e_url = 'http://w3af.org/api/pets'
        e_force_fuzzing_headers = []
        e_headers = Headers([('Content-Type', 'application/json')])
        e_body = '{"pet": {"age": 42}}'

        self.assertEqual(api_call.get_method(), 'POST')
        self.assertEqual(api_call.get_uri().url_string, e_url)
        self.assertEquals(api_call.get_headers(), e_headers)
        self.assertEqual(api_call.get_force_fuzzing_headers(), e_force_fuzzing_headers)
        self.assertEqual(api_call.get_data(), e_body)

        #
        # With validation enabled the parsing fails because there is a mising
        # required attribute
        #
        parser = OpenAPI(response, validate_swagger_spec=True)
        parser.parse()
        api_calls = parser.get_api_calls()
        self.assertEqual(len(api_calls), 0)

    def test_real_api_yaml(self):
        body = file(self.REAL_API_YAML).read()
        headers = Headers({'Content-Type': 'application/yaml'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.yaml'),
                                URL('http://moth/swagger.yaml'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        e_api_calls = [('GET',
                        u'https://w3af.org/bankid/tokens/4271a25e-7211-4306-b527-46196eb2af28',
                        Headers([(u'Content-Type', u'application/json')]),
                        ''),
                       ('POST',
                        u'https://w3af.org/bankid/tokens',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('POST',
                        u'https://w3af.org/bankid/tokens',
                        Headers([(u'Content-Type', u'application/json'), (u'Authorization', u'FrAmE30.')]),
                        '{"body": {"orderRef": "e475f288-4e9b-43ea-966c-d3912e7a25b2"}}'),
                       ('POST',
                        u'https://w3af.org/bankid/orders',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('POST',
                        u'https://w3af.org/bankid/orders',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": {"pid": "191212121212"}}'),
                       ('GET',
                        u'https://w3af.org/persons/3419/partners',
                        Headers([(u'Content-Type', u'application/json')]),
                        ''),
                       ('GET',
                        u'https://w3af.org/persons/3419/partners',
                        Headers([(u'Authorization', u'FrAmE30.'), (u'Content-Type', u'application/json')]),
                        ''),
                       ('GET',
                        u'https://w3af.org/persons/3419/partners/3419',
                        Headers([(u'Content-Type', u'application/json')]),
                        ''),
                       ('GET',
                        u'https://w3af.org/persons/3419/partners/3419',
                        Headers([(u'Authorization', u'FrAmE30.'), (u'Content-Type', u'application/json')]),
                        ''),
                       ('GET',
                        u'https://w3af.org/persons/3419',
                        Headers([(u'Content-Type', u'application/json')]),
                        ''),
                       ('GET',
                        u'https://w3af.org/persons/3419',
                        Headers([(u'Authorization', u'FrAmE30.'), (u'Content-Type', u'application/json')]),
                        ''),
                       ('POST',
                        u'https://w3af.org/persons/3419/partners',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('POST',
                        u'https://w3af.org/persons/3419/partners',
                        Headers([(u'Content-Type', u'application/json'), (u'Authorization', u'FrAmE30.')]),
                        '{"body": {"partner": "19101010****", "termsAccepted": false}}'),
                       ('PATCH',
                        u'https://w3af.org/persons/3419',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('PATCH',
                        u'https://w3af.org/persons/3419',
                        Headers([(u'Content-Type', u'application/json'), (u'Authorization', u'FrAmE30.')]),
                        '{"body": {"termsAccepted": false}}'),
                       ('PUT',
                        u'https://w3af.org/persons/3419/partners/3419',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('PUT',
                        u'https://w3af.org/persons/3419/partners/3419',
                        Headers([(u'Content-Type', u'application/json'), (u'Authorization', u'FrAmE30.')]),
                        '{"body": {"partner": "19101010****", "termsAccepted": false}}'),
                       ('POST',
                        u'https://w3af.org/events',
                        Headers([(u'Content-Type', u'application/json')]),
                        '{"body": null}'),
                       ('POST',
                        u'https://w3af.org/events',
                        Headers([(u'Content-Type', u'application/json'), (u'Authorization', u'FrAmE30.')]),
                        '{"body": {"event": "start doktor24"}}')
                       ]

        self.assertEqual(19, len(api_calls))

        for api_call in api_calls:
            method = api_call.get_method()
            headers = api_call.get_headers()
            data = api_call.get_data()

            uri = api_call.get_uri().url_string

            _tuple = (method, uri, headers, data)
            self.assertIn(_tuple, e_api_calls)

    def test_can_parse_content_type_no_keywords(self):
        # JSON content type
        # Does NOT contain keywords
        http_resp = self.generate_response('{}')
        self.assertFalse(OpenAPI.can_parse(http_resp))

    def test_can_parse_content_type_with_keywords(self):
        # JSON content type
        # Contains keywords
        # Invalid JSON format
        http_resp = self.generate_response('"')
        self.assertFalse(OpenAPI.can_parse(http_resp))

    def test_can_parse_invalid_yaml_with_keywords(self):
        # Yaml content type
        # Contains keywords
        # Invalid yaml format
        http_resp = self.generate_response('{}', 'application/yaml')
        self.assertFalse(OpenAPI.can_parse(http_resp))

    def test_content_type_match_true(self):
        http_resp = self.generate_response('{}')
        self.assertTrue(OpenAPI.content_type_match(http_resp))

    def test_content_type_match_false(self):
        http_resp = self.generate_response('', 'image/jpeg')
        self.assertFalse(OpenAPI.content_type_match(http_resp))

    def test_matches_any_keyword_true(self):
        http_resp = self.generate_response('{"consumes": "application/json"}')
        self.assertTrue(OpenAPI.matches_any_keyword(http_resp))

    def test_matches_any_keyword_false(self):
        http_resp = self.generate_response('{"none": "fail"}')
        self.assertFalse(OpenAPI.matches_any_keyword(http_resp))

    def test_is_valid_json_or_yaml_true(self):
        http_resp = self.generate_response('{}')
        self.assertTrue(OpenAPI.is_valid_json_or_yaml(http_resp))

        http_resp = self.generate_response('', 'application/yaml')
        self.assertTrue(OpenAPI.is_valid_json_or_yaml(http_resp))

    def test_is_valid_json_or_yaml_false(self):
        http_resp = self.generate_response('"', 'image/jpeg')
        self.assertFalse(OpenAPI.is_valid_json_or_yaml(http_resp))

    def generate_response(self, specification_as_string, content_type='application/json'):
        url = URL('http://www.w3af.com/swagger.json')
        headers = Headers([('content-type', content_type)])
        return HTTPResponse(200, specification_as_string, headers,
                            url, url, _id=1)

    # Check if the OpenAPI parser can extract all api calls from a json
    # file that is missing the license name (which is required if license
    # attribute is specified)
    def test_missing_license_name(self):
        body = file(self.MISSING_LICENSE).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        expected_api_calls = 5
        self.assertEqual(expected_api_calls, len(api_calls))

        first_api_call = api_calls[0]
        uri = first_api_call.get_uri().url_string

        expected_uri = 'http://1.2.3.4/api/prod/2.0/employees/3419'

        self.assertEqual(expected_uri, uri)

    def test_issue_210(self):
        body = file(self.ISSUE_210_API_YAML).read()
        headers = Headers({'Content-Type': 'application/yaml'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.yaml'),
                                URL('http://moth/swagger.yaml'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        expected_api_calls = 19
        self.assertEqual(expected_api_calls, len(api_calls))

        first_api_call = api_calls[0]
        uri = first_api_call.get_uri().url_string

        expected_uri = 'https://api.domain.com/domain/tokens'

        self.assertEqual(expected_uri, uri)
