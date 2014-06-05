# -*- encoding: utf-8 -*-
"""
test_lru.py

Copyright 2014 Andres Riancho

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

from w3af.core.controllers.misc.lru import LRU


class TestLRU(unittest.TestCase):
    def test_basic_lru(self):
        lru_test = LRU(4)
        lru_test['1'] = 1
        lru_test['2'] = 1
        lru_test['3'] = 1
        lru_test['4'] = 1

        # Adding one more, the '1' should go away
        lru_test['5'] = 1
        self.assertNotIn('1', lru_test)
        self.assertIn('5', lru_test)

    def test_keyerror(self):
        lru_test = LRU(4)
        self.assertRaises(KeyError, lru_test.__getitem__, '3')