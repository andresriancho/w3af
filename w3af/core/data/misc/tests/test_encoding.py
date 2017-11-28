# -*- coding: utf-8 -*-
"""
test_encoding.py

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

from w3af.core.data.misc.encoding import is_known_encoding, ESCAPED_CHAR, HTML_ENCODE
from w3af.core.data.misc.encoding import smart_unicode


class TestEncoding(unittest.TestCase):

    def test_is_known_encoding_true(self):
        self.assertTrue(is_known_encoding('utf-8'))

    def test_is_known_encoding_false(self):
        self.assertFalse(is_known_encoding('andres-16'))

    def test_escaped_char_empty(self):
        decoded = ''.decode('utf-8', errors=ESCAPED_CHAR)
        self.assertEqual(decoded, '')

    def test_escaped_char_no_error(self):
        decoded = 'ábc'.decode('utf-8', errors=ESCAPED_CHAR)
        self.assertEqual(decoded, u'ábc')

    def test_escaped_char_error_escape_char(self):
        decoded = '\xff'.decode('utf-8', errors=ESCAPED_CHAR)
        self.assertEqual(decoded, '\\xff')

    def test_escaped_char_error_html_encode(self):
        decoded = '\xff'.decode('utf-8', errors=HTML_ENCODE)
        self.assertEqual(decoded, '&#xff')

    def test_atilde(self):
        self.assertEquals(smart_unicode('á'), u'á')
