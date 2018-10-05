# -*- coding: utf-8 -*-
"""
test_json_container.py

Copyright 2014 Andres Riancho

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
import pickle
import unittest
import copy

from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.utils.token import DataToken

STRING = '"abc"'
NUMBER = '1'
ARRAY = '["abc", 3, 2.1]'
ARRAY_NULL = '["abc", null, null]'
OBJECT = '{"key": "value", "second_key": "second_value"}'
COMPLEX_OBJECT = '{"key": "value", "second_key": ["abc", 3, 2.1]}'
OBJECT_NULL = '{"key": null}'


class TestJSONContainer(unittest.TestCase):
    
    def test_basic(self):
        jcont = JSONContainer(COMPLEX_OBJECT)
        dcc_tokens = [(dcc, token) for dcc, token in jcont.iter_bound_tokens()]

        for dcc, token in dcc_tokens:
            self.assertIsInstance(dcc, JSONContainer)
            self.assertIsInstance(token, DataToken)
            self.assertIs(token, dcc.token)

        EXPECTED_TOKENS = [('object-second_key-list-0-string', 'abc'),
                           ('object-key-string', 'value')]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_object_null_value(self):
        jcont = JSONContainer(OBJECT_NULL)
        dcc_tokens = [(dcc, token) for dcc, token in jcont.iter_bound_tokens()]

        for dcc, token in dcc_tokens:
            self.assertIsInstance(dcc, JSONContainer)
            self.assertIsInstance(token, DataToken)
            self.assertIs(token, dcc.token)

        EXPECTED_TOKENS = [('object-key-null', None)]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_iter_bound_tokens_array(self):
        jcont = JSONContainer(ARRAY)
        dcc_tokens = [(dcc, token) for dcc, token in jcont.iter_bound_tokens()]

        for dcc, token in dcc_tokens:
            self.assertIsInstance(dcc, JSONContainer)
            self.assertIsInstance(token, DataToken)
            self.assertIs(token, dcc.token)

        EXPECTED_TOKENS = [('list-0-string', 'abc')]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_iter_bound_tokens_modify_during_iter(self):
        jcont = JSONContainer(ARRAY)
        idx = None
        tokens = []

        for idx, (dcc, token) in enumerate(jcont.iter_bound_tokens()):
            self.assertIsInstance(dcc, JSONContainer)
            self.assertIsInstance(token, DataToken)
            self.assertIs(token, dcc.token)

            token.set_value('xyz')
            tokens.append(token)

        self.assertEqual(idx, 0)

        EXPECTED_TOKENS = [('list-0-string', 'xyz')]
        token_data = [(t.get_name(), t.get_value()) for t in tokens]

        self.assertEqual(EXPECTED_TOKENS, token_data)
        self.assertEqual(str(dcc), ARRAY.replace('abc', 'xyz'))

    def test_is_json_true(self):
        self.assertTrue(JSONContainer.is_json('1'))
        self.assertTrue(JSONContainer.is_json('"abc"'))
        self.assertTrue(JSONContainer.is_json('{"abc": 3}'))

    def test_is_json_false(self):
        self.assertFalse(JSONContainer.is_json('x'))

    def test_copy_container_no_token(self):
        dc = JSONContainer(COMPLEX_OBJECT)
        dc_copy = copy.deepcopy(dc)
        self.assertEqual(dc, dc_copy)

    def test_copy_container_with_token(self):
        jcont = JSONContainer(ARRAY)
        dcc_tokens = [(dcc, token) for dcc, token in jcont.iter_bound_tokens()]

        dc, token = dcc_tokens[0]
        self.assertIsNotNone(dc.get_token())

        dc_copy = copy.deepcopy(dc)
        self.assertIsNotNone(dc_copy.get_token())

    def test_headers(self):
        jcont = JSONContainer(COMPLEX_OBJECT)

        e_headers = [('Content-Type', 'application/json')]
        self.assertEquals(jcont.get_headers(), e_headers)

        jcont.set_header('Content-Type', 'application/vnd.w3af+json')
        e_headers = [('Content-Type', 'application/vnd.w3af+json')]
        self.assertEquals(jcont.get_headers(), e_headers)

        jcont.set_header('X-Foo-Header', 'Bar')
        e_headers = [('Content-Type', 'application/vnd.w3af+json'), ('X-Foo-Header', 'Bar')]
        self.assertEquals(jcont.get_headers(), e_headers)

        headers = {'Content-Type': 'application/vnd.w3af+json', 'X-Foo-Header': 'Bar'}
        jcont = JSONContainer(COMPLEX_OBJECT, headers)

        e_headers = [('Content-Type', 'application/vnd.w3af+json'), ('X-Foo-Header', 'Bar')]
        self.assertEquals(jcont.get_headers(), e_headers)

        jcont.set_header('X-Foo-Header', '42')
        e_headers = [('Content-Type', 'application/vnd.w3af+json'), ('X-Foo-Header', '42')]
        self.assertEquals(jcont.get_headers(), e_headers)

        jcont = JSONContainer(COMPLEX_OBJECT, None)
        e_headers = [('Content-Type', 'application/json')]
        self.assertEquals(jcont.get_headers(), e_headers)

    def test_headers_immutable(self):
        jcont = JSONContainer(OBJECT)

        e_headers = [('Content-Type', 'application/json')]
        headers = jcont.get_headers()
        self.assertEquals(headers, e_headers)

        headers.append(('X-Foo-Header', 'Bar'))
        self.assertEquals(jcont.get_headers(), e_headers)

    def test_wrong_headers(self):
        jcont = JSONContainer(COMPLEX_OBJECT)

        with self.assertRaises(TypeError):
            jcont.set_header(1, 'Foo')

        with self.assertRaises(TypeError):
            jcont.set_header('Foo', 1)

        with self.assertRaises(TypeError):
            JSONContainer(COMPLEX_OBJECT, 'Foo')

        with self.assertRaises(TypeError):
            JSONContainer(COMPLEX_OBJECT, [])

    def test_pickle(self):
        original = JSONContainer(COMPLEX_OBJECT)

        e_headers = [('Content-Type', 'application/json')]
        self.assertEquals(original.get_headers(), e_headers)

        clone = pickle.loads(pickle.dumps(original))
        self.assertEquals(original, clone)
        self.assertEquals(clone.get_headers(), e_headers)

        original = JSONContainer(COMPLEX_OBJECT)
        original.set_header('Content-Type', 'application/vnd.w3af+json')

        e_headers = [('Content-Type', 'application/vnd.w3af+json')]
        self.assertEquals(original.get_headers(), e_headers)

        clone = pickle.loads(pickle.dumps(original))
        self.assertEquals(original, clone)
        self.assertEquals(clone.get_headers(), e_headers)

        original = JSONContainer(COMPLEX_OBJECT)
        original.set_header('X-Foo-Header', 'Bar')

        e_headers = [('Content-Type', 'application/json'), ('X-Foo-Header', 'Bar')]
        self.assertEquals(original.get_headers(), e_headers)

        clone = pickle.loads(pickle.dumps(original))
        self.assertEquals(original, clone)
        self.assertEquals(clone.get_headers(), e_headers)
