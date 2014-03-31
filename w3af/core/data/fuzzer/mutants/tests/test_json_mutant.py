"""
test_json_mutant.py

Copyright 2006 Andres Riancho

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

from w3af.core.data.parsers.url import URL
from w3af.core.data.request.JSONRequest import JSONPostDataRequest
from w3af.core.data.fuzzer.mutants.json_mutant import (JSONMutant, is_json,
                                                  _fuzz_json, _make_json_mutants)


class TestQSMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {}
        self.payloads = ['abc', '53']

    def test_is_json_int(self):
        self.assertTrue(is_json('1'))

    def test_is_json_str(self):
        self.assertTrue(is_json('"a"'))

    def test_is_json_lst(self):
        self.assertTrue(is_json('["a", "b"]'))

    def test_is_json_dict(self):
        self.assertTrue(is_json('{"a": "b"}'))

    def test_is_json_not(self):
        self.assertFalse(is_json('a=b'))

    def test_is_json_not_2(self):
        self.assertFalse(is_json('a=b&d=3'))

    def test_fuzz_json_int(self):
        expected = [(53, 1)]
        generated = _fuzz_json(self.payloads, 1, False)
        self.assertEqual(generated, expected)

    def test_fuzz_json_str(self):
        expected = [('abc', 'str'), ('53', 'str')]
        generated = _fuzz_json(self.payloads, 'str', False)
        self.assertEqual(generated, expected)

    def test_fuzz_json_dict(self):
        expected = [({'a': 'abc', 'c': 'd'}, 'b'),
                    ({'a': '53', 'c': 'd'}, 'b'),
                    ({'a': 'b', 'c': 'abc'}, 'd'),
                    ({'a': 'b', 'c': '53'}, 'd')]
        generated = _fuzz_json(self.payloads, {"a": "b", "c": "d"}, False)
        self.assertEqual(generated, expected)

    def test_fuzz_json_list(self):
        expected = [(['abc', 'b'], 'a'),
                    (['53', 'b'], 'a'),
                    (['a', 'abc'], 'b'),
                    (['a', '53'], 'b')]
        generated = _fuzz_json(self.payloads, ['a', 'b'], False)
        self.assertEqual(generated, expected)

    def test_make_json_mutants(self):
        freq = JSONPostDataRequest(URL('http://www.w3af.com/?id=3'))

        generated_mutants = _make_json_mutants(freq, self.payloads, [],
                                               False, {"a": "b", "c": "d"})

        self.assertEqual(len(generated_mutants), 4, generated_mutants)

        m0 = generated_mutants[0]
        self.assertEqual(m0.get_data(), '{"a": "abc", "c": "d"}')

        m1 = generated_mutants[1]
        self.assertEqual(m1.get_data(), '{"a": "53", "c": "d"}')

        m2 = generated_mutants[2]
        self.assertEqual(m2.get_data(), '{"a": "b", "c": "abc"}')

        m3 = generated_mutants[3]
        self.assertEqual(m3.get_data(), '{"a": "b", "c": "53"}')

    def test_json_mutant_create_mutants(self):
        freq = JSONPostDataRequest(URL('http://www.w3af.com/?id=3'))
        freq.set_dc({"a": "b", "c": "d"})

        generated_mutants = JSONMutant.create_mutants(freq, self.payloads, [],
                                                      False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 4, generated_mutants)

        m0 = generated_mutants[0]
        self.assertEqual(m0.get_data(), '{"a": "abc", "c": "d"}')

        m1 = generated_mutants[1]
        self.assertEqual(m1.get_data(), '{"a": "53", "c": "d"}')

        m2 = generated_mutants[2]
        self.assertEqual(m2.get_data(), '{"a": "b", "c": "abc"}')

        m3 = generated_mutants[3]
        self.assertEqual(m3.get_data(), '{"a": "b", "c": "53"}')

    def test_json_mutant_create_mutants_not(self):
        freq = JSONPostDataRequest(URL('http://www.w3af.com/?id=3'))
        freq.set_dc('a=1&b=foo')

        generated_mutants = JSONMutant.create_mutants(freq, self.payloads, [],
                                                      False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)
