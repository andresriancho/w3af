# -*- coding: UTF-8 -*-
"""
test_specification.py

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
from w3af.core.data.parsers.doc.open_api.specification import SpecificationHandler
from w3af.core.data.parsers.doc.open_api.tests.example_specifications import (NoParams,
                                                                              IntParamQueryString,
                                                                              StringParam,
                                                                              ArrayStringItems,
                                                                              ArrayIntItems,
                                                                              ModelParam,
                                                                              ModelParamNested,
                                                                              ModelParamNestedLoop,
                                                                              ArrayModelItems)


class TestSpecification(unittest.TestCase):
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

        (spec, api_resource_name, resource,
         operation_name, operation, parameters) = data[0]

        self.assertEqual(api_resource_name, 'random')
        self.assertEqual(operation_name, 'get_random')
        self.assertEqual(operation.consumes, [])
        self.assertEqual(operation.produces, [])
        self.assertEqual(operation.params, {})
        self.assertEqual(operation.path_name, '/random')

    def test_simple_int_param_in_qs(self):
        specification_as_string = IntParamQueryString().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        data = [d for d in handler.get_api_information()]

        self.assertEqual(len(data), 1)

        (spec, api_resource_name, resource,
         operation_name, operation, parameters) = data[0]

        self.assertEqual(api_resource_name, 'random')
        self.assertEqual(operation_name, 'get_random')
        self.assertEqual(operation.consumes, [])
        self.assertEqual(operation.produces, [])
        self.assertEqual(operation.params, {})
        self.assertEqual(operation.path_name, '/random')

    def test_simple_int_param_in_json_post_data(self):
        raise NotImplementedError

    def test_simple_string_param_in_qs(self):
        raise NotImplementedError

    def test_array_string_items_param_in_json(self):
        raise NotImplementedError

    def test_array_int_items_param_in_json(self):
        raise NotImplementedError

    def test_model_param_in_json(self):
        specification_as_string = ModelParam().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

        for data in handler.get_api_information():
            pass

    def test_model_param_nested_in_json(self):
        specification_as_string = ModelParam().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

    def test_model_param_nested_loop_in_json(self):
        specification_as_string = ModelParam().get_specification()
        http_response = self.generate_response(specification_as_string)
        handler = SpecificationHandler(http_response)

    def test_array_model_items_param_in_json(self):
        raise NotImplementedError
