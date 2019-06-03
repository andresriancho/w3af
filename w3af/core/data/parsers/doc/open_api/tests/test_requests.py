# -*- coding: UTF-8 -*-
"""
test_requests.py

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
import unittest

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.doc.open_api.requests import RequestFactory
from w3af.core.data.parsers.doc.open_api.specification import SpecificationHandler
from w3af.core.data.parsers.doc.open_api.tests.example_specifications import (NoParams,
                                                                              IntParamQueryString,
                                                                              IntParamPath,
                                                                              StringParamQueryString,
                                                                              StringParamHeader,
                                                                              IntParamJson,
                                                                              IntParamWithExampleJson,
                                                                              ArrayStringItemsQueryString,
                                                                              ComplexDereferencedNestedModel,
                                                                              DereferencedPetStore,
                                                                              NestedModel,
                                                                              ArrayModelItems)


class TestRequests(unittest.TestCase):
    def generate_response(self, specification_as_string):
        url = URL('http://www.w3af.com/swagger.json')
        headers = Headers([('content-type', 'application/json')])
        return HTTPResponse(200, specification_as_string, headers,
                            url, url, _id=1)

    def test_no_params(self):
        specification_as_string = NoParams().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/random'
        e_headers = Headers()

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_raw_data(), '')

    def test_string_param_header(self):
        specification_as_string = StringParamHeader().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)

        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets'
        e_headers = Headers([('X-Foo-Header', '56'),
                             ('Content-Type', 'application/json')])
        e_data = ''

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

    def test_simple_int_param_in_qs(self):
        specification_as_string = IntParamQueryString().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is not
        # required, thus we get two operations, one for the parameter with
        # a value and another without the parameter
        self.assertEqual(len(data), 2)

        #
        # Assertions on call #1
        #
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://w3af.org/api/pets'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '')

        #
        # Assertions on call #2
        #
        data_i = data[1]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://w3af.org/api/pets?limit=42'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '')

    def test_simple_int_param_in_path(self):
        specification_as_string = IntParamPath().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/pets/42'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_raw_data(), '')

    def test_simple_string_param_in_qs(self):
        specification_as_string = StringParamQueryString().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets?q=Spam or Eggs?'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_raw_data(), '')

    def test_array_string_items_param_in_qs(self):
        specification_as_string = ArrayStringItemsQueryString().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets?tags=56'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_raw_data(), '')

    def test_model_with_int_param_json(self):
        specification_as_string = IntParamJson().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '{"pet": {"count": 42}}')

    def test_model_with_int_param_json_example_value(self):
        specification_as_string = IntParamWithExampleJson().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets'
        e_headers = Headers([('Content-Type', 'application/json')])

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), '{"pet": {"count": 666999}}')

    def test_no_model_json_object_complex_nested_in_body(self):
        specification_as_string = ComplexDereferencedNestedModel().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/pets'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = ('{"pet": {"owner": {"name": {"last": "Smith", "first": "56"},'
                  ' "address": {"postalCode": "90210", "street1": "Bonsai Street 123",'
                  ' "street2": "Bonsai Street 123", "state": "AK",'
                  ' "city": "Buenos Aires"}}, "type": "cat", "name": "John",'
                  ' "birthdate": "2017-06-30"}}')

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

    def test_array_with_model_items_param_in_json(self):
        specification_as_string = ArrayModelItems().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)

        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://petstore.swagger.io/api/pets'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = '{"pets": [{"tag": "7", "name": "John"}]}'

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

    def test_model_param_nested_allOf_in_json(self):
        specification_as_string = NestedModel().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        self.assertEqual(len(data), 1)

        # The specification says that this query string parameter is
        # required and there is only one parameter, so there is no second
        # operation with the optional parameters filled in.
        self.assertEqual(len(data), 1)

        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://w3af.org/api/pets'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = '{"pet": {"tag": "7", "name": "John", "id": 42}}'

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

    def test_dereferenced_pet_store(self):
        # See: dereferenced_pet_store.json , which was generated using
        # http://bigstickcarpet.com/swagger-parser/www/index.html#

        specification_as_string = DereferencedPetStore().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]
        self.assertEqual(len(data), 3)

        #
        # Assertions on call #1
        #
        data_i = data[0]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/pets/John'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = ''

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

        #
        # Assertions on call #2
        #
        data_i = data[1]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/pets'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = ''

        self.assertEqual(fuzzable_request.get_method(), 'GET')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)

        #
        # Assertions on call #3
        #
        data_i = data[2]

        factory = RequestFactory(*data_i)
        fuzzable_request = factory.get_fuzzable_request()

        e_url = 'http://www.w3af.com/pets'
        e_headers = Headers([('Content-Type', 'application/json')])
        e_data = ('{"pet": {"owner": {"name": {"last": "Smith", "first": "56"},'
                  ' "address": {"postalCode": "90210", "street1": "Bonsai Street 123",'
                  ' "street2": "Bonsai Street 123", "state": "AK",'
                  ' "city": "Buenos Aires"}}, "type": "cat", "name": "John",'
                  ' "birthdate": "2017-06-30"}}')

        self.assertEqual(fuzzable_request.get_method(), 'POST')
        self.assertEqual(fuzzable_request.get_uri().url_string, e_url)
        self.assertEqual(fuzzable_request.get_headers(), e_headers)
        self.assertEqual(fuzzable_request.get_data(), e_data)
