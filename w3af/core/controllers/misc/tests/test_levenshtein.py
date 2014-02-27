# -*- encoding: utf-8 -*-
"""
test_levenshtein.py

Copyright 2012 Andres Riancho

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

from w3af.core.controllers.misc.levenshtein import relative_distance_boolean, relative_distance


class TestLevenshtein(unittest.TestCase):

    def test_all(self):
        acceptance_tests = []
        acceptance_tests.append(('a', 'a', 1.0))
        acceptance_tests.append(('a', 'a', 0.1))
        acceptance_tests.append(('a', 'a', 0.0))

        acceptance_tests.append(('a', 'b', 1.0))
        acceptance_tests.append(('a', 'b', 0.1))
        acceptance_tests.append(('a', 'b', 0.0))

        acceptance_tests.append(('a', 'ab', 1.0))
        acceptance_tests.append(('a', 'ab', 0.1))

        acceptance_tests.append(('a', 'b', 0.0000000000000000001))
        acceptance_tests.append(('a', 'b' * 100, 1.0))

        acceptance_tests.append(('a', 'ab', 0.66666666666))
        acceptance_tests.append(('a', 'aab', 0.5))
        acceptance_tests.append(('a', 'aaab', 0.4))
        acceptance_tests.append(('a', 'aaaab', 0.33333333333333333333333333333333333333333333333333333333))

        acceptance_tests.append(('a' * 25, 'a', 1.0))
        acceptance_tests.append(('aaa', 'aa', 1.0))
        acceptance_tests.append(('a', 'a', 1.0))

        acceptance_tests.append(('a' * 25, 'a', 0.076923076923076927))
        acceptance_tests.append(('aaa', 'aa', 0.8))

        acceptance_tests.append(('a', 'a', 0.0))

        for e, d, f in acceptance_tests:
            res1 = relative_distance_boolean(e, d, f)
            res2 = relative_distance(e, d) >= f
            
            msg = 'relative_distance_boolean and relative_distance returned'\
                  ' different results for the same parameters:\n'\
                  '    - %s\n'\
                  '    - %s\n'\
                  '    - Threshold: %s\n'\
            
            self.assertEqual(res1, res2, msg % (e, d, f))
