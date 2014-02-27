"""
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

"""
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.search_engines.bing import bing
from w3af.core.data.url.extended_urllib import ExtendedUrllib


@attr('internet')
class test_bing(unittest.TestCase):

    def setUp(self):
        self.bing_se = bing(ExtendedUrllib())

    def test_get_links_results_few(self):
        self.query, self.limit = ('two and half man', 60)
        self.get_links_results()
        
    def test_get_links_results_many(self):
        self.query, self.limit = ('big bang theory', 200)
        self.get_links_results()

    def get_links_results(self):
        results = self.bing_se.get_n_results(self.query, self.limit)
        
        # I want to get real results
        domains = set([r.URL.get_domain() for r in results])
        self.assertGreater(len(domains), 3, results)

        # URLs should be unique
        urls = [r.URL for r in results]
        repeated_urls = [u for u in urls if urls.count(u)>1]
        self.assertEqual(len(repeated_urls), 0,
                         'These are the repeated URLs: %s' % repeated_urls)
