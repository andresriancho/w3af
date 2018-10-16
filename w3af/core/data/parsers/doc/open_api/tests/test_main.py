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
import datetime
import os
import unittest

from w3af import ROOT_PATH
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.parsers.doc.open_api.parameters import ParameterValues
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

    PARAMETER_VALUES = os.path.join(DATA_PATH, 'parameter_values.yaml')
    MULTIPLE_HEADERS_PARAMETER_VALUES = os.path.join(DATA_PATH, 'multiple_headers_parameter_values.yaml')
    PETSTORE_SIMPLE_PARAMETER_VALUES = os.path.join(DATA_PATH, 'petstore_simple_parameter_values.yaml')

    def test_json_pet_store(self):
        # http://petstore.swagger.io/v2/swagger.json
        body = file(self.SWAGGER_JSON).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

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
                           ' "status": "available", "name": "John",'
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
                           ' "complete": true, "petId": 42, "id": 42, "quantity": 42}}')

        e_api_calls = [
            ('GET',  '/pet/findByStatus?status=available', json_headers, ''),
            ('POST', '/pet/42/uploadImage', multipart_headers, ''),
            ('POST', '/pet/42', url_encoded_headers, ''),
            ('POST', '/pet', json_headers, expected_body_1),
            ('GET',  '/pet/42', json_headers, ''),
            ('GET',  '/pet/42', json_api_headers, ''),
            ('GET',  '/pet/findByTags?tags=56', json_headers, ''),
            ('PUT',  '/pet', json_headers, expected_body_1),
            ('PUT',  '/user/John8212', json_headers, expected_body_2),
            ('POST', '/user/createWithList', json_headers, expected_body_3),
            ('POST', '/user', json_headers, expected_body_2),
            ('GET',  '/user/John8212', json_headers, ''),
            ('GET',  '/user/login?username=John8212&password=FrAmE30.', json_headers, ''),
            ('GET',  '/user/logout', Headers(), ''),
            ('POST', '/user/createWithArray', json_headers, expected_body_3),
            ('GET',  '/store/order/2', json_headers, ''),
            ('GET',  '/store/inventory', json_headers, ''),
            ('GET',  '/store/inventory', json_api_headers, ''),
            ('POST', '/store/order', json_headers, expected_body_4),
        ]

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

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()
        self.assertEquals(api_calls, [])

    def test_disabling_headers_discovery(self):
        body = file(self.MULTIPLE_PATHS_AND_HEADERS).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

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

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()
        self.assertEqual(len(api_calls), 0)

        parser = OpenAPI(response, no_validation=True)
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

    def test_loading_parameter_values(self):
        values = ParameterValues()
        values.load_from_file(self.PARAMETER_VALUES)
        self.assertIsNotNone(values)
        self.assertEquals(values.get('/users/{user-id}', 'user-id'), [1234567])
        self.assertEquals(values.get('/users/{user-id}', 'X-First-Name'), ['John', 'Bill'])
        self.assertEquals(values.get('/users', 'user-id'), [1234567])
        self.assertEquals(values.get('/users', 'birth-date'), [datetime.date(2000, 1, 2)])
        self.assertEquals(values.get('/does_not_exist', 'user-id'), [])
        self.assertEquals(values.get('/users', 'does-not-exist'), [])

        values.set('/users/{user-id}', 'last-name', ['Python'])
        self.assertEquals(values.get('/users/{user-id}', 'last-name'), ['Python'])
        values.set('/new', 'foo-bar', ['bar', 'foo'])
        self.assertEquals(values.get('/new', 'foo-bar'), ['bar', 'foo'])

        with self.assertRaises(ValueError):
            values.set('/foo', 'bar', 'wrong')

    def test_petstore_simple_with_parameter_values(self):
        body = file(self.PETSTORE_SIMPLE).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)
        values = ParameterValues()
        values.load_from_file(self.PETSTORE_SIMPLE_PARAMETER_VALUES)

        parser = OpenAPI(response, custom_parameter_values=values)
        parser.parse()
        api_calls = parser.get_api_calls()

        api_calls.sort(by_path)

        self.assertEqual(len(api_calls), 7)

        e_pets_headers_1 = Headers([
            ('Content-Type', 'application/json')])

        e_body_1 = '{"pet": {"tag": "17", "name": "Joe"}}'
        e_body_2 = '{"pet": {"tag": "123", "name": "Jan"}}'

        e_pets_force_fuzzing_headers = []

        url_root = 'http://petstore.swagger.io/api'

        e_api_calls = [
            ('GET',  '/pets',                       e_pets_headers_1, e_pets_force_fuzzing_headers, ''),
            ('GET',  '/pets?limit=1&tags=Buddy',    e_pets_headers_1, e_pets_force_fuzzing_headers, ''),
            ('GET',  '/pets?limit=5&tags=Buddy',    e_pets_headers_1, e_pets_force_fuzzing_headers, ''),
            ('POST', '/pets',                       e_pets_headers_1, e_pets_force_fuzzing_headers, e_body_1),
            ('POST', '/pets',                       e_pets_headers_1, e_pets_force_fuzzing_headers, e_body_2),
            ('GET',  '/pets/3333',                  e_pets_headers_1, e_pets_force_fuzzing_headers, ''),
            ('GET',  '/pets/4444',                  e_pets_headers_1, e_pets_force_fuzzing_headers, '')
        ]

        for api_call in api_calls:
            method = api_call.get_method()
            headers = api_call.get_headers()
            force_fuzzing_headers = api_call.get_force_fuzzing_headers()
            data = api_call.get_data()

            uri = api_call.get_uri().url_string
            uri = uri.replace(url_root, '')

            data = (method, uri, headers, force_fuzzing_headers, data)

            self.assertIn(data, e_api_calls)

    def test_json_multiple_paths_and_headers_with_parameter_values(self):
        body = file(self.MULTIPLE_PATHS_AND_HEADERS).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)
        values = ParameterValues()
        values.load_from_file(self.MULTIPLE_HEADERS_PARAMETER_VALUES)

        parser = OpenAPI(response, custom_parameter_values=values)
        parser.parse()
        api_calls = parser.get_api_calls()

        api_calls.sort(by_path)

        self.assertEqual(len(api_calls), 9)

        e_cats_headers_1 = Headers([
            ('X-Awesome-Header', '2017'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])
        e_cats_headers_2 = Headers([
            ('X-Awesome-Header', '2018'),
            ('X-Foo-Header', 'foo'),
            ('Content-Type', 'application/json')])
        e_pets_headers_1 = Headers([
            ('X-Foo-Header', '10101'),
            ('Content-Type', 'application/json')])
        e_pets_headers_2 = Headers([
            ('X-Bar-Header', 'cat'),
            ('X-Foo-Header', '10101'),
            ('Content-Type', 'application/json')])
        e_pets_headers_3 = Headers([
            ('X-Bar-Header', 'dog'),
            ('X-Foo-Header', '10101'),
            ('Content-Type', 'application/json')])

        e_cats_force_fuzzing_headers = ['X-Awesome-Header', 'X-Foo-Header']
        e_pets_force_fuzzing_headers = ['X-Bar-Header', 'X-Foo-Header']

        url_root = 'http://w3af.org/api'

        e_api_calls = [
            ('GET', '/cats', e_cats_headers_1, e_cats_force_fuzzing_headers),
            ('GET', '/cats', e_cats_headers_2, e_cats_force_fuzzing_headers),
            ('GET', '/cats?limit=1', e_cats_headers_1, e_cats_force_fuzzing_headers),
            ('GET', '/cats?limit=1', e_cats_headers_2, e_cats_force_fuzzing_headers),
            ('GET', '/cats?limit=1000', e_cats_headers_1, e_cats_force_fuzzing_headers),
            ('GET', '/cats?limit=1000', e_cats_headers_2, e_cats_force_fuzzing_headers),
            ('GET', '/pets', e_pets_headers_1, e_pets_force_fuzzing_headers),
            ('GET', '/pets', e_pets_headers_2, e_pets_force_fuzzing_headers),
            ('GET', '/pets', e_pets_headers_3, e_pets_force_fuzzing_headers),
        ]

        for api_call in api_calls:
            method = api_call.get_method()
            headers = api_call.get_headers()
            force_fuzzing_headers = api_call.get_force_fuzzing_headers()

            uri = api_call.get_uri().url_string
            uri = uri.replace(url_root, '')

            data = (method, uri, headers, force_fuzzing_headers)

            self.assertIn(data, e_api_calls)

    @staticmethod
    def generate_response(specification_as_string, content_type='application/json'):
        url = URL('http://www.w3af.com/swagger.json')
        headers = Headers([('content-type', content_type)])
        return HTTPResponse(200, specification_as_string, headers,
                            url, url, _id=1)
