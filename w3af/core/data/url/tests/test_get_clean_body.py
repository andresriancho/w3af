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
import urllib

from w3af.core.data.url.helpers import (get_clean_body,
                                        apply_multi_escape_table,
                                        extend_escape_table_with_uppercase,
                                        ESCAPE_TABLE)
from w3af.core.data.parsers.doc.url import URL
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

    def test_get_clean_body_encoded(self):
        payload = 'hello/world'

        body = 'abc %s def' % urllib.urlencode({'a': payload})
        url = URL('http://w3af.com')
        headers = Headers([('Content-Type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url)

        freq = FuzzableRequest(URL('http://w3af.com/?a=1'))
        created_mutants = FakeMutant.create_mutants(freq, [payload], [],
                                                    False, {})

        mutant = created_mutants[0]

        clean_body = get_clean_body(mutant, response)

        self.assertEqual(clean_body, 'abc a= def')
        self.assertIsInstance(clean_body, unicode)

    def test_get_clean_body_double_encoded(self):
        payload = 'hello/world'

        body = 'abc %s def' % urllib.quote_plus(urllib.quote_plus(payload))
        url = URL('http://w3af.com')
        headers = Headers([('Content-Type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url)

        freq = FuzzableRequest(URL('http://w3af.com/?a=1'))
        created_mutants = FakeMutant.create_mutants(freq, [payload], [],
                                                    False, {})

        mutant = created_mutants[0]

        clean_body = get_clean_body(mutant, response)

        self.assertEqual(clean_body, 'abc  def')
        self.assertIsInstance(clean_body, unicode)


class TestExtendTable(unittest.TestCase):
    def test_trivial(self):
        et = extend_escape_table_with_uppercase(ESCAPE_TABLE)

        self.assertEqual(et['"'],
                         ['"', '&quot;', '&#x22;', '&#34;', '&#034;',
                          '%22', '%2522', '\\u0022', '\\"', '&QUOT;', '\\U0022'])

        self.assertEqual(et['='],
                         ['=', '&eq;', '&#x3d;', '&#61;', '&#061;', '%3d', '%253d',
                          '&EQ;', '&#x3D;', '%3D', '%253D'])


class TestApplyMultiEscapeTable(unittest.TestCase):
    def test_apply_multi_escape_table_0(self):
        escaped = apply_multi_escape_table('abc')
        escaped = [i for i in escaped]

        expected = ['abc']
        self.assertEqual(escaped, expected, escaped)

    def test_apply_multi_escape_table_1(self):
        escaped = apply_multi_escape_table(' ')
        escaped = [i for i in escaped]

        expected = [' ', '&nbsp;', '&#x20;', '&#32;', '&#032;', '+', '%20', '%2520']
        self.assertEqual(escaped, expected, escaped)

    def test_apply_multi_escape_table_2(self):
        escaped = apply_multi_escape_table(' &')
        escaped = [i for i in escaped]

        expected = [' &', '&nbsp;&', '&#x20;&', '&#32;&', '&#032;&', '+&', '%20&',
                    '%2520&', ' &amp;', '&nbsp;&amp;', '&#x20;&amp;', '&#32;&amp;',
                    '&#032;&amp;', '+&amp;', '%20&amp;', '%2520&amp;', ' &#x26;',
                    '&nbsp;&#x26;', '&#x20;&#x26;', '&#32;&#x26;', '&#032;&#x26;',
                    '+&#x26;', '%20&#x26;', '%2520&#x26;', ' &#38;', '&nbsp;&#38;',
                    '&#x20;&#38;', '&#32;&#38;', '&#032;&#38;', '+&#38;', '%20&#38;',
                    '%2520&#38;', ' &#038;', '&nbsp;&#038;', '&#x20;&#038;',
                    '&#32;&#038;', '&#032;&#038;', '+&#038;', '%20&#038;',
                    '%2520&#038;', ' %26', '&nbsp;%26', '&#x20;%26', '&#32;%26',
                    '&#032;%26', '+%26', '%20%26', '%2520%26', ' %2526', '&nbsp;%2526',
                    '&#x20;%2526', '&#32;%2526', '&#032;%2526', '+%2526', '%20%2526',
                    '%2520%2526']

        self.assertEqual(escaped, expected, escaped)
