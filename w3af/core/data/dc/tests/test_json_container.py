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
import unittest
import copy

from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.token import DataToken

STRING = '"abc"'
NUMBER = '1'
ARRAY = '["abc", 3, 2.1]'
ARRAY_NULL = '["abc", null, null]'
OBJECT = '{"key": "value", "second_key": "second_value"}'
COMPLEX_OBJECT = '{"key": "value", "second_key": ["abc", 3, 2.1]}'


class TestJSONContainer(unittest.TestCase):
    
    def test_basic(self):
        jcont = JSONContainer(COMPLEX_OBJECT)
        dcc_tokens = [(dcc, token) for dcc, token in jcont.iter_bound_tokens()]

        for dcc, token in dcc_tokens:
            self.assertIsInstance(dcc, JSONContainer)
            self.assertIsInstance(token, DataToken)

        EXPECTED_TOKENS = [('object-second_key-list-0-string', 'abc'),
                           ('object-second_key-list-1-number', 3),
                           ('object-second_key-list-2-number', 2.1),
                           ('object-key-string', 'value')]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_is_json_true(self):
        self.assertTrue(JSONContainer.is_json('1'))
        self.assertTrue(JSONContainer.is_json('"abc"'))
        self.assertTrue(JSONContainer.is_json('{"abc": 3}'))

    def test_is_json_false(self):
        self.assertFalse(JSONContainer.is_json('x'))

    def test_copy(self):
        dc = JSONContainer(COMPLEX_OBJECT)
        self.assertEqual(dc, copy.deepcopy(dc))