# -*- coding: utf-8 -*-
"""
test_get_clean_body.py

Copyright 2015 Andres Riancho

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

from w3af.core.data.url.helpers import get_clean_body
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.tests.test_mutant import FakeMutant


class TestGetCleanBody(unittest.TestCase):
    def test_get_clean_body_simple(self):
        payload = 'payload'

        body = 'abc %s def' % payload
        url = URL('http://w3af.com')
        headers = Headers([('Content-Type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url)


        freq = FuzzableRequest(URL('http://w3af.com/?a=1'))
        created_mutants = FakeMutant.create_mutants(freq, [payload], [],
                                                    False, {})

        mutant = created_mutants[0]

        clean_body = get_clean_body(mutant, response)

        self.assertEqual(clean_body, body.replace(payload, ''))
        self.assertIsInstance(clean_body, unicode)