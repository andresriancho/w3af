# -*- encoding: utf-8 -*-
"""
generic_filter_test.py

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
import random
import string

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.controllers.tests.pylint_plugins.decorator import only_if_subclass


class GenericFilterTest(unittest.TestCase):

    CAPACITY = None
    ERROR_RATE = None
    filter = None
    
    def setUp(self):
        # Init the seed to something fixed in order to have always the same
        # "random" numbers used.
        random.seed(20)

    @only_if_subclass
    def test_bloom_int(self):
        for i in xrange(0, self.CAPACITY):
            self.filter.add(i)
            
        # After understanding a little bit more about how bloom filters work,
        # I decided to comment this line. Given the probabilistic nature of
        # these filters, it might be the case that the length of the filter is
        # CAPACITY-1 (in other words, one insert failed because all the bits
        # were already set to 1) and that doesn't mean that the filter is
        # useless it just means that it's false positive rate is going up.
        #self.assertEqual( len(self.filter), self.CAPACITY)

        for i in xrange(0, self.CAPACITY):
            self.assertIn(i, self.filter)

        for i in xrange(0, self.CAPACITY / 2):
            r = random.randint(self.CAPACITY, self.CAPACITY * 2)
            self.assertNotIn(r, self.filter)

    @only_if_subclass
    def test_bloom_string(self):
        randomly_generated_strings = []

        for _ in xrange(0, self.CAPACITY):
            rnd = ''.join(random.choice(string.letters) for i in xrange(40))
            randomly_generated_strings.append(rnd)
            self.filter.add(rnd)

        for saved_str in randomly_generated_strings:
            self.assertIn(saved_str, self.filter)

        for i in string.letters:
            self.assertNotIn(i, self.filter)

        for saved_str in randomly_generated_strings:
            self.assertNotIn(saved_str[::-1], self.filter)

    @only_if_subclass
    def test_bloom_url_objects(self):        
        for i in xrange(0, self.CAPACITY):
            url_num = URL('http://moth/index%s.html' % i)
            self.filter.add(url_num)

        self.assertIn(url_num, self.filter)

        for i in string.letters:
            url_char = URL('http://moth/index%s.html' % i)
            self.assertNotIn(url_char, self.filter)

        for i in xrange(self.CAPACITY, self.CAPACITY * 2):
            url_char = URL('http://moth/index%s.html' % i)
            self.assertNotIn(url_char, self.filter)

    @only_if_subclass
    def test_unicode_string(self):
        unicode_string = u'¡'
        self.filter.add(unicode_string)
        
        self.assertIn(unicode_string, self.filter)

    @only_if_subclass
    def test_scale(self):
        if not isinstance(self.filter, ScalableBloomFilter):
            return
        
        count = 12500
        for i in xrange(0, count):
            self.filter.add(i)
        
        self.assertGreater(self.filter.capacity, count)
        
        self.assertEqual(self.filter.capacity, 15000)
        self.assertLessEqual(len(self.filter), count)
        
        self.assertLessEqual(
                             abs((len(self.filter) / float(count)) - 1.0),
                             self.filter.error_rate
                             )

