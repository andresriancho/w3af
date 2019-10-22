# -*- coding: utf-8 -*-
"""
test_headers.py

Copyright 2012 Andres Riancho

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

from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.utils.token import DataToken


class TestHeaders(unittest.TestCase):

    def test_empty(self):
        self.assertEquals(Headers([]), Headers([]))

    def test_false(self):
        self.assertFalse(Headers())

    def test_simple(self):
        headers = Headers([('a', 'b')])

        self.assertIn('a', headers)
        self.assertEqual(headers['a'], 'b')

    def test_raises(self):
        self.assertRaises(TypeError, Headers, {})
        
    def test_build_with_headers(self):
        headers = Headers([('a', 'b')])
        headers = Headers(headers)
        
        self.assertIn('a', headers)
        self.assertEqual(headers['a'], 'b')

    def test_str(self):
        headers = Headers([('a', 'b')])

        self.assertEqual(str(headers), 'a: b\r\n')

    def test_str_multi(self):
        headers = Headers([('a', 'b'), ('1', '2')])

        self.assertEqual(str(headers), 'a: b\r\n1: 2\r\n')

    def test_unicode(self):
        headers = Headers([('a', 'b')])

        self.assertEqual(unicode(headers), 'a: b\r\n')

    def test_str_strange(self):
        header_value = ''.join(chr(i) for i in xrange(256))
        headers = Headers([(u'Hola', header_value)])
        
        # I don't assert in a stricter way because the output depends on
        # smart_unicode which might change in the future
        self.assertIn('Hola: \x00\x01\x02', str(headers))
        
    def test_repeated_raises(self):
        self.assertRaises(TypeError, Headers, [('a', 'b'), ('a', '3')])

    def test_special_chars(self):
        headers = Headers([('á', 'ç')])

        self.assertIn(u'á', headers)
        self.assertEqual(headers[u'á'], u'ç')

    def test_special_chars_build(self):
        headers_initial = Headers([('á', 'ç')])
        headers_from_headers = Headers(headers_initial)
        
        self.assertIn(u'á', headers_from_headers)
        self.assertEqual(headers_from_headers[u'á'], u'ç')

    def test_add_later(self):
        headers = Headers([('a', 'b')])
        headers['c'] = '2'

        self.assertIn('a', headers)
        self.assertEqual(headers['a'], 'b')
        self.assertIn('c', headers)
        self.assertEqual(headers['c'], '2')

    def test_overwrite(self):
        headers = Headers([('a', 'b')])
        headers['a'] = '2'

        self.assertIn('a', headers)
        self.assertEqual(headers['a'], '2')

    def test_headers_case_sensitive(self):
        upper_headers = Headers([('Abc', 'b')])
        lower_headers = Headers([('abc', 'b')])

        self.assertNotEqual(upper_headers, lower_headers)

    def test_headers_update(self):
        abc_headers = Headers([('Abc', 'b')])
        def_headers = Headers([('def', '1')])

        abc_headers.update(def_headers)

        expected_headers = Headers([('Abc', 'b'), ('def', '1')])

        self.assertEqual(expected_headers, abc_headers)

    def test_headers_update_overlap(self):
        abc_headers = Headers([('Abc', 'b'), ('def', '2')])
        def_headers = Headers([('def', '1')])

        abc_headers.update(def_headers)

        expected_headers = Headers([('Abc', 'b'), ('def', '1')])

        self.assertEqual(expected_headers, abc_headers)

    def test_from_string(self):
        headers_from_str = Headers.from_string('a: b\r\n')
        headers_from_obj = Headers([('a', 'b')])
        self.assertEqual(headers_from_str, headers_from_obj)

    def test_to_str_from_string(self):
        headers_from_obj = Headers([('a', 'b')])
        headers_from_str = Headers.from_string(str(headers_from_obj))
        
        self.assertEqual(headers_from_str, headers_from_obj)

    def test_from_invalid_string(self):
        self.assertRaises(ValueError, Headers.from_string, 'ab')

    def test_headers_iget(self):
        upper_headers = Headers([('Abc', 'b')])

        value, real_header = upper_headers.iget('abc')

        self.assertEqual(value, 'b')
        self.assertEqual(real_header, 'Abc')

    def test_headers_idel(self):
        upper_headers = Headers([('Abc', 'b')])

        upper_headers.idel('abc')

        self.assertNotIn('Abc', upper_headers)

    def test_tokens_to_value(self):
        token = DataToken('a', 'b', ('a',))
        headers = Headers([('a', token)])

        headers.tokens_to_value()

        self.assertIn('a', headers)
        self.assertEqual(headers['a'], 'b')
        self.assertIsInstance(headers['a'], basestring)

    def test_copy_with_token(self):
        dc = Headers([('Abc', 'b')])

        dc.set_token(('Abc',))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())
        self.assertEqual(dc_copy.get_token().get_name(), 'Abc')