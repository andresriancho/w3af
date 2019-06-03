"""
test_utils.py

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

from w3af.core.data.fuzzer.utils import rand_alpha, rand_alnum, rand_number


class TestFuzzerUtils(unittest.TestCase):
    
    def test_rand_number(self):
        x = rand_number(length=1)
        self.assertIn(int(x), range(10))

        x = rand_number(length=2)
        self.assertIn(int(x), range(100))
    
        x = rand_number(length=3)
        self.assertIn(int(x), range(1000))

        x = rand_number(length=5)
        y = rand_number(length=5)
        z = rand_number(length=5)
        w = rand_number(length=5)
        self.assertTrue(x != y != z != w)
    
    def test_rand_alnum(self):
        x = rand_alnum(length=10)
        self.assertEqual(len(x), 10)
        
        x = rand_alnum(length=20)
        self.assertEqual(len(x), 20)
        
        x = rand_alnum(length=5)
        y = rand_alnum(length=5)
        z = rand_alnum(length=5)
        w = rand_alnum(length=5)
        self.assertTrue(x != y != z != w)

    def test_rand_alpha(self):
        x = rand_alpha(length=10)
        self.assertEqual(len(x), 10)
        
        x = rand_alpha(length=20)
        self.assertEqual(len(x), 20)
        
        x = rand_alpha(length=5)
        y = rand_alpha(length=5)
        z = rand_alpha(length=5)
        w = rand_alpha(length=5)
        self.assertTrue(x != y != z != w)

    def test_rand_alpha_with_seed(self):
        x = rand_alpha(length=10, seed=1)
        self.assertEqual(len(x), 10)

        y = rand_alpha(length=10, seed=1)
        self.assertEqual(len(y), 10)

        self.assertEqual(x, y)

        z = rand_alpha(length=10, seed=2)
        self.assertEqual(len(z), 10)

        self.assertNotEqual(y, z)
