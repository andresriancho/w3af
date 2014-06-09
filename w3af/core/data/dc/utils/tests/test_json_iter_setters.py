"""
test_json_iter_setters.py

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
import json

from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.utils.json_iter_setters import (json_iter_setters,
                                                       MutableWrapper,
                                                       json_complex_str,
                                                       KEY_NUMBER, KEY_STRING,
                                                       KEY_BOOLEAN, KEY_ARRAY,
                                                       KEY_OBJECT, KEY_NULL)
from w3af.core.data.dc.tests.test_json_container import (STRING, ARRAY, NUMBER,
                                                         OBJECT, COMPLEX_OBJECT)


class TestJSONIterSetters(unittest.TestCase):

    def test_mutable_json(self):
        json = JSONContainer.get_mutable_json(ARRAY)
        self.assertIsInstance(json, MutableWrapper)

    def test_int(self):
        json_data = JSONContainer.get_mutable_json(NUMBER)
        jis = [(k, v, s) for k, v, s in json_iter_setters(json_data)]

        self.assertEqual(len(jis), 1)

        k, v, s = jis[0]
        self.assertEqual(k, KEY_NUMBER)
        self.assertEqual(v, 1)
        self.assertTrue(callable(s))

        s(2)

        self.assertEqual(json_complex_str(json_data), '2')

    def test_string(self):
        json_data = JSONContainer.get_mutable_json(STRING)
        jis = [(k, v, s) for k, v, s in json_iter_setters(json_data)]

        self.assertEqual(len(jis), 1)

        k, v, s = jis[0]
        self.assertEqual(k, KEY_STRING)
        self.assertEqual(v, 'abc')
        self.assertTrue(callable(s))

        s('xyz')

        self.assertEqual(json_complex_str(json_data), '"xyz"')

    def test_array(self):
        json_data = JSONContainer.get_mutable_json(ARRAY)
        jis = [(k, v, s) for k, v, s in json_iter_setters(json_data)]

        self.assertEqual(len(jis), 3)

        k, v, s = jis[0]
        self.assertEqual(k, '-'.join([KEY_ARRAY, '0', KEY_STRING]))
        self.assertEqual(v, 'abc')
        self.assertTrue(callable(s))

        s('xyz')
        payload_array = ARRAY.replace('abc', 'xyz')
        self.assertEqual(json_complex_str(json_data), payload_array)

        k, v, s = jis[1]
        self.assertEqual(k, '-'.join([KEY_ARRAY, '1', KEY_NUMBER]))
        self.assertEqual(v, 3)
        self.assertTrue(callable(s))

        s(4.4)
        payload_array = payload_array.replace('3', '4.4')
        self.assertEqual(json_complex_str(json_data), payload_array)

        k, v, s = jis[2]
        self.assertEqual(k, '-'.join([KEY_ARRAY, '2', KEY_NUMBER]))
        self.assertEqual(v, 2.1)
        self.assertTrue(callable(s))

        s(3.3)
        payload_array = payload_array.replace('2.1', '3.3')
        self.assertEqual(json_complex_str(json_data), payload_array)

    def test_object(self):
        json_data = JSONContainer.get_mutable_json(OBJECT)
        jis = [(k, v, s) for k, v, s in json_iter_setters(json_data)]

        self.assertEqual(len(jis), 2)

        first_key = '-'.join([KEY_OBJECT, 'key', KEY_STRING])
        k, v, s = [(k, v, s) for (k, v, s) in jis if k == first_key][0]
        self.assertEqual(k, first_key)
        self.assertEqual(v, 'value')
        self.assertTrue(callable(s))

        s('xyz')
        payload_object = OBJECT.replace('"value"', '"xyz"')
        self.assertEqual(json.loads(json_complex_str(json_data)),
                         json.loads(payload_object))

        second_key = '-'.join([KEY_OBJECT, 'second_key', KEY_STRING])
        k, v, s = [(k, v, s) for (k, v, s) in jis if k == second_key][0]
        self.assertEqual(k, second_key)
        self.assertEqual(v, 'second_value')
        self.assertTrue(callable(s))

        s('spam')
        payload_object = payload_object.replace('second_value', 'spam')
        self.assertEqual(json.loads(json_complex_str(json_data)),
                         json.loads(payload_object))

    def test_complex_object(self):
        json_data = JSONContainer.get_mutable_json(COMPLEX_OBJECT)
        jis = [(k, v, s) for k, v, s in json_iter_setters(json_data)]

        self.assertEqual(len(jis), 4)
        payload_complex = COMPLEX_OBJECT[:]

        for idx, (k, v, s) in enumerate(jis):
            if isinstance(v, int):
                new_value = idx
            elif isinstance(v, float):
                new_value = float(idx)
            else:
                new_value = str(idx)

            s(new_value)
            payload_complex = payload_complex.replace(str(v), str(new_value))

        self.assertEqual(json.loads(json_complex_str(json_data)),
                         json.loads(payload_complex))