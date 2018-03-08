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
import unittest

from nose.plugins.skip import SkipTest

from w3af import ROOT_PATH
from w3af.core.controllers.misc.diff import diff, chunked_diff


class TestDiff(unittest.TestCase):

    DATA = os.path.join(ROOT_PATH, 'core', 'controllers', 'misc', 'tests', 'data')

    def test_middle(self):
        self.assertEqual(diff('123456', '123a56'), ('4', 'a'))

    def test_start(self):
        self.assertEqual(diff('yes 123abc', 'no 123abc'), ('yes', 'no'))

    def test_end(self):
        self.assertEqual(diff('123abc yes', '123abc no'), ('yes', 'no'))

    def test_nono(self):
        self.assertEqual(diff('123abc yes', 'no 123abc no'), ('yes', 'no no'))

    @SkipTest
    def test_xml(self):
        """
        Comment the @SkipTest and then run:

        nosetests --with-timer -s -v -x w3af/core/controllers/misc/tests/test_diff.py
        """
        a = file(os.path.join(self.DATA, 'source.xml')).read()
        b = file(os.path.join(self.DATA, 'target.xml')).read()

        # This takes ~2.5 seconds on my workstation
        diff(a, b)


class TestDiffInChunks(unittest.TestCase):

    DATA = os.path.join(ROOT_PATH, 'core', 'controllers', 'misc', 'tests', 'data')

    @SkipTest
    def test_xml(self):
        """
        Comment the @SkipTest and then run:

        nosetests --with-timer -s -v -x w3af/core/controllers/misc/tests/test_diff.py
        """
        a = file(os.path.join(self.DATA, 'source.xml')).read()
        b = file(os.path.join(self.DATA, 'target.xml')).read()

        # This takes ~0.07 seconds on my workstation
        chunked_diff(a, b)

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

    def test_different_separator(self):
        a = 'X\tB\nC'
        b = 'A<B\nC'
        self.assertEqual(chunked_diff(a, b), ('X', 'A'))
