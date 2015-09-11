# -*- encoding: utf-8 -*-
"""
test_average_ratio.py

Copyright 2015 Andres Riancho

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

from w3af.core.data.fuzzy_cmp.average_ratio import average_ratio
from w3af.core.data.fuzzy_cmp.fuzzy_string_cmp import relative_distance


class TestAverageRatio(unittest.TestCase):
    def test_all_equal(self):
        inputs = ['abc', 'abc', 'abc', 'abc', 'abc']
        self.assertEqual(average_ratio(inputs), 1.0)

    def test_very_equal(self):
        inputs = ['abcdef1', 'abcdef2', 'abcdef3', 'abcdef4', 'abcdef5']

        expected_avg = round(relative_distance(inputs[0], inputs[1]), 5)
        average = round(average_ratio(inputs), 5)

        self.assertEqual(average, expected_avg)

    def test_not_enough(self):
        inputs = ['abc', 'abc', 'abc']
        self.assertRaises(ValueError, average_ratio, inputs)

    def test_odd_one_out(self):
        inputs = ['abc', 'abc', 'abc', 'abc', 'def']
        self.assertRaises(ValueError, average_ratio, inputs)

    def test_average_too_low(self):
        inputs = ['a1', 'a2', 'a3', 'a4', 'a5']
        self.assertRaises(ValueError, average_ratio, inputs)
