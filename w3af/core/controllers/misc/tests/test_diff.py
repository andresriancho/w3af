# -*- encoding: utf-8 -*-
"""
test_diff.py

Copyright 2018 Andres Riancho

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

from w3af.core.controllers.misc.diff import chunked_diff, diff_dmp


class TestChunkedDiff(unittest.TestCase):

    def test_equal(self):
        self.assertEqual(chunked_diff('123456', '123456'), ('', ''))

    def test_middle(self):
        self.assertEqual(chunked_diff('123456', '123a56'),
                         ('4', 'a'))

    def test_start(self):
        self.assertEqual(chunked_diff('yes 123abc', 'no 123abc'),
                         ('yes', 'no'))

    def test_end(self):
        self.assertEqual(chunked_diff('123abc\nyes', '123abc\nno'),
                         ('yes', 'no'))

    def test_nono(self):
        self.assertEqual(chunked_diff('123abc\nyes', 'no\n123abc\nno'),
                         ('yes', 'nono'))

    def test_middle(self):
        a = 'A\nB\nC'
        b = 'A\nX\nC'
        self.assertEqual(chunked_diff(a, b), ('B', 'X'))

    def test_all_no_sep(self):
        a = 'ABC'
        b = 'AXC'
        self.assertEqual(chunked_diff(a, b), ('ABC', 'AXC'))

    def test_middle_not_aligned(self):
        a = 'A\nB\nC'
        b = 'A\nXY\nC'
        self.assertEqual(chunked_diff(a, b), ('B', 'XY'))

    def test_empty(self):
        self.assertEqual(chunked_diff('', ''), ('', ''))

    def test_start(self):
        a = 'X\nB\nC'
        b = 'A\nB\nC'
        self.assertEqual(chunked_diff(a, b), ('X', 'A'))

    def test_special_chars(self):
        a = 'X\tB\nC'
        b = 'A<B\nC'
        self.assertEqual(chunked_diff(a, b), ('X', 'A'))


class TestDiffDMP(unittest.TestCase):

    def test_equal(self):
        self.assertEqual(diff_dmp('123456', '123456'), ('', ''))

    def test_middle(self):
        self.assertEqual(diff_dmp('123456', '123a56'),
                         ('4', 'a'))

    def test_start(self):
        self.assertEqual(diff_dmp('yes 123abc', 'no 123abc'),
                         ('yes', 'no'))

    def test_end(self):
        self.assertEqual(diff_dmp('123abc yes', '123abc no'),
                         ('yes', 'no'))

    def test_nono(self):
        self.assertEqual(diff_dmp('123abc yes', 'no 123abc no'),
                         ('yes', 'no \nno'))

    def test_middle(self):
        a = 'A\nB\nC'
        b = 'A\nX\nC'
        self.assertEqual(diff_dmp(a, b), ('B', 'X'))

    def test_all_no_sep(self):
        a = 'ABC'
        b = 'AXC'
        self.assertEqual(diff_dmp(a, b), ('B', 'X'))

    def test_middle_not_aligned(self):
        a = 'A\nB\nC'
        b = 'A\nXY\nC'
        self.assertEqual(diff_dmp(a, b), ('B', 'XY'))

    def test_empty(self):
        self.assertEqual(diff_dmp('', ''), ('', ''))

    def test_start(self):
        a = 'X\nB\nC'
        b = 'A\nB\nC'
        self.assertEqual(diff_dmp(a, b), ('X', 'A'))

    def test_special_chars(self):
        a = 'X\tB\nC'
        b = 'A<B\nC'
        self.assertEqual(diff_dmp(a, b), ('X\t', 'A<'))
