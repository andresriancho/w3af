# -*- coding: UTF-8 -*-
"""
test_fuzzy_equal_for_diff.py

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
import re
import unittest
import random

from w3af.core.controllers.core_helpers.not_found.fuzzy_equal_for_diff import fuzzy_equal_for_diff


class Test404FuzzyEqualForDiff(unittest.TestCase):

    IS_EQUAL_RATIO = 0.90

    def get_body(self, unique_parts):
        # Do not increase this 50 too much, it will exceed the xurllib max
        # HTTP response body length
        parts = [re.__doc__]
        parts = parts * 50

        parts.extend(unique_parts)

        rnd = random.Random()
        rnd.seed(1)
        rnd.shuffle(parts)

        body = '\n'.join(parts)

        return body

    def test_empty(self):
        diff_x = ''
        diff_y = ''

        args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

        self.assertTrue(fuzzy_equal_for_diff(*args))

    def test_medium(self):
        diff_x = ('fc76bcc057fc40d092e9742cec14c98a\n'
                  'fc76bcc057fc40d092e9742cec14c98a\n'
                  'MJT-2Rx4k4ZuI5R5DCHJ_Mx6Krc\n'
                  'fc76bcc057fc40d092e9742cec14c98a\n')

        diff_y = ('0e7b2e00d5ee46718258ae6ed5e2b315\n'
                  '0e7b2e00d5ee46718258ae6ed5e2b315\n'
                  '0e7b2e00d5ee46718258ae6ed5e2b315\n')

        args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

        self.assertTrue(fuzzy_equal_for_diff(*args))

    def test_large(self):
        diff_x = self.get_body([])
        diff_y = self.get_body([])

        args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

        self.assertTrue(fuzzy_equal_for_diff(*args))

    def test_large_very_diff(self):
        tests = [
            (1, True),
            (10, True),
            (50, True),
            (100, True),
            (200, True),
            (1500, False),
        ]

        for num_lines, expected_result in tests:
            diff_x = self.get_body([])
            diff_y = self.get_body(['Hello world this an added line for a test'] * num_lines)

            args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

            self.assertEqual(fuzzy_equal_for_diff(*args),
                             expected_result,
                             'Failed at test %s' % num_lines)

    def test_empty_add_text_lines(self):
        tests = [
            (1, False),
            (2, False),
            (3, False),
            (4, False),
            (5, False),
        ]

        for num_lines, expected_result in tests:
            diff_x = ''
            diff_y = '\n'.join(['hello world'] * num_lines)

            args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

            self.assertEqual(fuzzy_equal_for_diff(*args),
                             expected_result,
                             'Failed at test %s' % num_lines)

    def test_empty_add_hash_lines(self):
        tests = [
            (1, True),
            (2, True),
            (3, True),
            (10, True),
            (100, True),
        ]

        for num_lines, expected_result in tests:
            diff_x = ''
            diff_y = '\n'.join(['0e7b2e00d5ee46718258ae6ed5e2b315'] * num_lines)

            args = (diff_x, diff_y, self.IS_EQUAL_RATIO)

            self.assertEqual(fuzzy_equal_for_diff(*args),
                             expected_result,
                             'Failed at test %s' % num_lines)
