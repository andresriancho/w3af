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

from w3af.core.controllers.misc.diff import diff


class TestDiff(unittest.TestCase):
    def test_middle(self):
        self.assertEqual(diff('123456', '123a56'), ('4', 'a'))

    def test_start(self):
        self.assertEqual(diff('yes 123abc', 'no 123abc'), ('yes', 'no'))

    def test_end(self):
        self.assertEqual(diff('123abc yes', '123abc no'), ('yes', 'no'))

    def test_nono(self):
        self.assertEqual(diff('123abc yes', 'no 123abc no'), ('yes', 'no no'))
