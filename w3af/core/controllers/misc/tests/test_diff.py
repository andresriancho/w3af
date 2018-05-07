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
import os
import time
import unittest

from w3af import ROOT_PATH
from w3af.core.controllers.misc.diff import diff


class TestDiff(unittest.TestCase):

    DATA = os.path.join(ROOT_PATH, 'core', 'controllers', 'misc', 'tests', 'data')

    def test_middle(self):
        self.assertEqual(diff('123456', '123a56'),
                         ('4', 'a'))

    def test_start(self):
        self.assertEqual(diff('yes 123abc', 'no 123abc'),
                         ('yes', 'no'))

    def test_end(self):
        self.assertEqual(diff('123abc yes', '123abc no'),
                         ('yes', 'no'))

    def test_nono(self):
        self.assertEqual(diff('123abc yes', 'no 123abc no'),
                         ('yes', 'no no'))

    def test_xml(self):
        """
        Before using https://pypi.org/project/diff-match-patch/ this test took
        around 2 seconds to run. Now it only takes 0.0056 sec!

        nosetests --with-timer -s -v -x w3af/core/controllers/misc/tests/test_diff.py
        """
        a = file(os.path.join(self.DATA, 'source.xml')).read()
        b = file(os.path.join(self.DATA, 'target.xml')).read()

        start = time.time()

        diff(a, b)

        spent = time.time() - start
        self.assertGreater(1.0, spent)

    def test_diff_large_different_responses(self):
        """
        Same here, this test took 8 seconds to run, and now it takes 0.4704s!
        """
        large_file_1 = ''
        large_file_2 = ''
        _max = 10000

        for i in xrange(_max):
            large_file_1 += 'A' * i
            large_file_1 += '\n'

        for i in xrange(_max):
            if i == _max - 3:
                large_file_2 += 'B' * i
            else:
                large_file_2 += 'A' * i

            large_file_2 += '\n'

        start = time.time()

        body1, body2 = diff(large_file_1, large_file_2)

        spent = time.time() - start
        self.assertGreater(1.0, spent)

        self.assertEqual(body1, 'A' * (_max - 3))
        self.assertEqual(body2, 'B' * (_max - 3))

    def test_middle(self):
        a = 'A\nB\nC'
        b = 'A\nX\nC'
        self.assertEqual(diff(a, b), ('B', 'X'))

    def test_all_no_sep(self):
        a = 'ABC'
        b = 'AXC'
        self.assertEqual(diff(a, b), ('B', 'X'))

    def test_middle_not_aligned(self):
        a = 'A\nB\nC'
        b = 'A\nXY\nC'
        self.assertEqual(diff(a, b), ('B', 'XY'))

    def test_empty(self):
        self.assertEqual(diff('', ''), ('', ''))

    def test_start(self):
        a = 'X\nB\nC'
        b = 'A\nB\nC'
        self.assertEqual(diff(a, b), ('X', 'A'))

    def test_special_chars(self):
        a = 'X\tB\nC'
        b = 'A<B\nC'
        self.assertEqual(diff(a, b), ('X\t', 'A<'))

    def test_large_equal_responses(self):
        large_file = ''

        for i in xrange(10000):
            large_file += 'A' * i
            large_file += '\n'

        start = time.time()

        body1, body2 = diff(large_file, large_file)

        self.assertEqual(body1, '')
        self.assertEqual(body2, '')

        spent = time.time() - start
        self.assertGreater(1.0, spent)

