# -*- coding: utf-8 -*-
"""
test_plain.py

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

from w3af.core.data.dc.generic.plain import PlainContainer


class TestPlainContainer(unittest.TestCase):
    
    def test_basic(self):
        dc = PlainContainer('abc', 'text/plain')
        
        self.assertEqual('abc', str(dc))
        self.assertNotIn('abc', dc)
        self.assertEqual(dc.content_type_header_value, 'text/plain')
        self.assertEqual(dc.get_headers(), [('content-type', 'text/plain')])

    def test_iter_tokens(self):
        dc = PlainContainer('abc', 'text/plain')
        tokens = [t for t in dc.iter_tokens()]

        self.assertEqual(tokens, [])

    def test_iter_bound_tokens(self):
        dc = PlainContainer('abc', 'text/plain')
        tokens = [t for t in dc.iter_bound_tokens()]

        self.assertEqual(tokens, [])

    def test_iter_setters(self):
        dc = PlainContainer('abc', 'text/plain')
        tokens = [t for t in dc.iter_setters()]

        self.assertEqual(tokens, [])

    def test_set_token(self):
        dc = PlainContainer('abc', 'text/plain')
        # Content is not a token
        self.assertRaises(RuntimeError, dc.set_token, 'abc')

    def test_is_variant_all_equal(self):
        dc1 = PlainContainer('abc', 'text/plain')
        dc2 = PlainContainer('abc', 'text/plain')

        self.assertTrue(dc1.is_variant_of(dc2))

    def test_is_variant_diff_headers(self):
        dc1 = PlainContainer('abc', 'text/plain')
        dc2 = PlainContainer('abc', 'text/xml')

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_get_headers_none(self):
        dc = PlainContainer('abc')

        self.assertEqual(dc.get_headers(), [])
