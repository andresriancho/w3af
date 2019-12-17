# -*- coding: utf-8 -*-
"""
test_helpers.py

Copyright 2019 Andres Riancho

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

from w3af.core.data.url.helpers import remove_using_lower_case


class TestRemoveUsingLowerCase(unittest.TestCase):
    def test_all_lower(self):
        result = remove_using_lower_case('hello world',
                                         'hello world',
                                         'world')
        expected = ('hello ', 'hello ')
        self.assertEqual(expected, result)

    def test_mixed(self):
        result = remove_using_lower_case('hello World',
                                         'hello world',
                                         'world')
        expected = ('hello ', 'hello ')
        self.assertEqual(expected, result)

    def test_mixed_multiple_replace(self):
        result = remove_using_lower_case('hello World world',
                                         'hello world world',
                                         'world')
        expected = ('hello ', 'hello ')
        self.assertEqual(expected, result)
