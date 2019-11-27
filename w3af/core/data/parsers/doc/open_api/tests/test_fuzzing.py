# -*- coding: UTF-8 -*-
"""
test_fuzzing.py

Copyright 2019 Andres Riancho

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
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.open_api import OpenAPI
from w3af.core.data.url.HTTPResponse import HTTPResponse


class TestOpenAPIFuzzing(unittest.TestCase):
    DATA_PATH = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc', 'open_api', 'tests', 'data')

    INVALID_TOKEN_PATH = os.path.join(DATA_PATH, 'invalid-token-path.json')

    def test_fuzing_on_invalid_token_path(self):
        body = file(self.INVALID_TOKEN_PATH).read()
        headers = Headers({'Content-Type': 'application/json'}.items())
        response = HTTPResponse(200, body, headers,
                                URL('http://moth/swagger.json'),
                                URL('http://moth/swagger.json'),
                                _id=1)

        self.assertTrue(OpenAPI.can_parse(response))

        parser = OpenAPI(response)
        parser.parse()
        api_calls = parser.get_api_calls()

        for api_call in api_calls:

            fake_mutants = create_mutants(api_call, [''])

            for mutant in fake_mutants:
                create_mutants(mutant.get_fuzzable_request(),
                               [''],
                               fuzzable_param_list=[mutant.get_token_name()])
