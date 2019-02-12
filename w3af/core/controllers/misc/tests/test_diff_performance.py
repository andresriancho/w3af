# -*- encoding: utf-8 -*-
"""
test_diff_performance.py

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
from __future__ import print_function

import os
import time
import unittest

from w3af import ROOT_PATH
from w3af.core.controllers.misc.diff import chunked_diff, diff_difflib, diff_dmp


class TestDiffPerformance(unittest.TestCase):

    DATA = os.path.join(ROOT_PATH, 'core', 'controllers', 'misc', 'tests', 'data')
    FUNCTIONS = [chunked_diff, diff_dmp]
    ROUNDS = 5

    def test_xml(self):
        self._generic_runner(self._run_test_xml)

    def test_diff_large_different_responses(self):
        self._generic_runner(self._run_diff_large_different_responses)

    def test_large_equal_responses(self):
        self._generic_runner(self._run_large_equal_responses)

    def _generic_runner(self, test_func):
        result = {}

        for func in self.FUNCTIONS:
            start = time.time()

            for _ in xrange(self.ROUNDS):
                test_func(func)

            spent = time.time() - start
            result[func.__name__] = spent

        self._print_result(result)

    def _print_result(self, result):
        results = result.items()
        results.sort(lambda a, b: a[1] < b[1])

        print()

        for func, spent in results:
            print('%s: %.2f' % (func, spent))

        print()

    def _run_test_xml(self, diff):
        a = file(os.path.join(self.DATA, 'source.xml')).read()
        b = file(os.path.join(self.DATA, 'target.xml')).read()

        diff(a, b)

    def _run_diff_large_different_responses(self, diff):
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

        diff(large_file_1, large_file_2)

    def _run_large_equal_responses(self, diff):
        large_file = ''

        for i in xrange(10000):
            large_file += 'A' * i
            large_file += '\n'

        diff(large_file, large_file)
