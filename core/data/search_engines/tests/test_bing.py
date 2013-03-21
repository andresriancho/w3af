'''
test_bing.py

Copyright 2006 Andres Riancho

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

'''
import random
import unittest

from core.data.search_engines.bing import bing
from core.data.url.extended_urllib import ExtendedUrllib


class test_bing(unittest.TestCase):

    def setUp(self):
        self.query, self.limit = random.choice([('big bang theory', 200),
                                                ('two and half man', 40),
                                                ('doctor house', 60)])
        self.bing_se = bing(ExtendedUrllib())

    def test_get_links_results(self):
        results = self.bing_se.get_n_results(self.query, self.limit)
        
        # Len of results must be le. than limit
        self.assertLessEqual(len(results), self.limit)

        # I want to get some results...
        self.assertTrue(len(results) >= 10, results)
        self.assertTrue(
            len(set([r.URL.get_domain() for r in results])) >= 3, results)

        # URLs should be unique
        urls = [r.URL for r in results]
        repeated_urls = [u for u in urls if urls.count(u)>1]
        self.assertEqual(len(repeated_urls), 0,
                         'These are the repeated URLs: %s' % repeated_urls)
