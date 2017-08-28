# -*- coding: UTF-8 -*-
"""
test_open_api.py

Copyright 2017 Andres Riancho

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
import unittest
import os

from w3af import ROOT_PATH
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.open_api import OpenAPI


class TestOpenAPI(unittest.TestCase):

    DATA_PATH = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc', 'tests', 'data')

    SWAGGER_JSON = os.path.join(DATA_PATH, 'swagger.json')
    PETSTORE_SIMPLE = os.path.join(DATA_PATH, 'petstore-simple.json')
    PETSTORE_EXPANDED = os.path.join(DATA_PATH, 'petstore-simple.json')

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
        api_calls = parser.get_forms()

        e_api_calls = ['1']

        self.assertEqual(api_calls, e_api_calls)

    def test_open_api_v20(self):
        # https://github.com/OAI/OpenAPI-Specification/blob/master/examples/v2.0/json/petstore-simple.json
        raise NotImplementedError

    def test_pet_store_yaml(self):
        # https://github.com/OAI/OpenAPI-Specification/blob/master/examples/v2.0/yaml/petstore-expanded.yaml
        raise NotImplementedError

    def test_can_parse_content_type_no_keywords(self):
        # JSON content type
        # Does NOT contain keywords
        raise NotImplementedError

    def test_can_parse_content_type_with_keywords(self):
        # JSON content type
        # Contains keywords
        # Invalid JSON format
        raise NotImplementedError

    def test_can_parse_invalid_yaml_with_keywords(self):
        # Yaml content type
        # Contains keywords
        # Invalid yaml format
        raise NotImplementedError