'''
test_seekfile_bloom.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import random
import unittest
import string

from nose.plugins.attrib import attr

from core.data.bloomfilter.seekfile_bloom import FileSeekBloomFilter


class TestSeekFileBloomFilter(unittest.TestCase):

    @attr('smoke')
    def test_bloom_int(self):
        f = FileSeekBloomFilter(capacity=10000, error_rate=0.001)

        for i in xrange(0, f.capacity / 3):
            already_in_filter = f.add(i)
            self.assertFalse(already_in_filter)
            
        self.assertEqual(len(f), f.capacity / 3)
        
        for i in xrange(0, f.capacity ):
            r = random.randint(0, (f.capacity-3) / 3)
            self.assertTrue(r in f, r)

        for i in xrange(0, f.capacity ):
            r = random.randint(f.capacity,f.capacity * 2)
            self.assertFalse(r in f, r)

    def test_bloom_int_over_capacity(self):
        
        def add_too_many():
            f = FileSeekBloomFilter(capacity=10, error_rate=0.001)
            for i in xrange(0, f.capacity * 2):
                _ = f.add(i)
            
        self.assertRaises(IndexError, add_too_many)
    
    @attr('smoke')
    def test_bloom_string(self):
        f = FileSeekBloomFilter(capacity=10000, error_rate=0.001)

        for i in xrange(0, f.capacity):
            rnd = ''.join(random.choice(string.letters) for i in xrange(40))
            _ = f.add(rnd)

        self.assertEqual(rnd in f, True)

        for i in string.letters:
            self.assertEqual(i in f, False)

        self.assertEqual(rnd in f, True)

