# -*- coding: utf-8 -*-
"""
test_utils.py

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

from w3af.core.data.statistics.utils import drop_outliers


class TestStatsUtils(unittest.TestCase):
    def test_drop_outliers_huge(self):
        data = [3, 4, 2, 5, 4, 3, 4, 5, 99]
        data_without_outliers = drop_outliers(data)

        self.assertEqual(data_without_outliers,
                         [3, 4, 2, 5, 4, 3, 4, 5])

    def test_drop_outliers_med(self):
        data = [3, 4, 2, 5, 15, 3, 4, 5]
        data_without_outliers = drop_outliers(data)

        self.assertEqual(data_without_outliers,
                         [3, 4, 2, 5, 3, 4, 5])

    def test_drop_outliers_not_removed(self):
        data = [1, 1, 1]
        data_without_outliers = drop_outliers(data)

        self.assertEqual(data_without_outliers, data)

    def test_drop_outliers_not_removed_2(self):
        data = [3, 4, 3, 4, 3, 4]
        data_without_outliers = drop_outliers(data)

        self.assertEqual(data_without_outliers, data)

    def test_drop_outliers_not_removed_with_offset(self):
        data = [3, 4, 3, 4, 3, 4, 2]
        data_without_outliers = drop_outliers(data, offset=1.85)

        self.assertEqual(data_without_outliers,
                         [3, 4, 3, 4, 3, 4, 2])

    def test_drop_outliers_remove(self):
        data = [0.31, 0.21, 2.02]
        data_without_outliers = drop_outliers(data, offset=1.4)

        self.assertEqual(data_without_outliers,
                         [0.31, 0.21])
