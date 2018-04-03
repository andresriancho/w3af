# -*- coding: utf-8 -*-
"""
test_token.py

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

from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.misc.encoding import smart_unicode


class TestToken(unittest.TestCase):
    NAME = 'name'
    VALUE = 'value'
    PATH = 'path'
    PAYLOAD = 'payload'

    def test_basic(self):
        token = DataToken(self.NAME, self.VALUE, self.PATH)

        self.assertEqual(token.get_name(), self.NAME)
        self.assertEqual(token.get_value(), self.VALUE)
        self.assertEqual(token.get_original_value(), self.VALUE)
        self.assertEqual(token.get_path(), self.PATH)

    def test_copy(self):
        original = DataToken(self.NAME, self.VALUE, self.PATH)

        token = copy.deepcopy(original)

        self.assertEqual(token.get_name(), self.NAME)
        self.assertEqual(token.get_value(), self.VALUE)
        self.assertEqual(token.get_original_value(), self.VALUE)
        self.assertEqual(token.get_path(), self.PATH)

    def test_copy_after_change(self):
        original = DataToken(self.NAME, self.VALUE, self.PATH)
        original.set_value(self.PAYLOAD)

        token = copy.deepcopy(original)

        self.assertEqual(token.get_name(), self.NAME)
        self.assertEqual(token.get_value(), self.PAYLOAD)
        self.assertEqual(token.get_original_value(), self.VALUE)
        self.assertEqual(token.get_path(), self.PATH)

    def test_invalid_utf8(self):
        invalid_utf8 = '\xf3'
        token = DataToken(self.NAME, invalid_utf8, self.PATH)

        self.assertRaises(UnicodeDecodeError, unicode, token)

        encoded_token = smart_unicode(token)
        self.assertEqual(encoded_token, u'\xf3')

    def test_unicodeencodeerror(self):
        _unicode = u'í'
        token = DataToken(self.NAME, _unicode, self.PATH)

        self.assertEqual(str(token), 'í')
