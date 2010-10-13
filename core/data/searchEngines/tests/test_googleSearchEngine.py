'''
googleSearchEngine.py

Copyright 2006 Andres Riancho

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
import re
import unittest

from core.data.searchEngines.googleSearchEngine import googleSearchEngine, \
    GAjaxSearch, GStandardSearch, GMobileSearch, GSetSearch
from core.data.url.httpResponse import httpResponse
from core.data.url.xUrllib import xUrllib
from core.data.parsers import urlParser


# Global vars
HEADERS = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)'}
# TODO: This needs to be mocked up!
URL_OPENER = xUrllib()
URL_OPEN_FUNC = lambda url: URL_OPENER.GET(url, headers=HEADERS,
                                            useCache=True, grepResult=False)
URL_REGEX = re.compile('((http|https)://([a-zA-Z0-9_:@\-\./]*?)/[^ \n\r\t"\'<>]*)')

class test_googleSearchEngine(unittest.TestCase):
    
    def setUp(self):
        self.query, self.limit = random.choice([('big bang theory', 200),
                                                ('two and half man', 37),
                                                ('doctor house', 55)])
        self.gse = googleSearchEngine(URL_OPENER)
        
    
    def test_get_links_results_len(self):
        # Len of results must be ge. than limit
        results = self.gse.getNResults(self.query, self.limit)
        self.assertTrue(len(results) <= self.limit)
    
    def test_get_links_results_unique(self):
        # URLs should be unique
        results = self.gse.getNResults(self.query, self.limit)
        self.assertTrue(len(results) == len(set(r.URL for r in results)))
    
    def test_page_body(self):
        # Verify that responses' body contains at least one word in query
        responses = self.gse.getNResultPages(self.query, self.limit)
        words = self.query.split()
        for resp in responses:
            found = False
            html_text = resp.getBody()
            for word in words:
                if word in html_text:
                    found = True
                    break
            self.assertTrue(found)
            
        

class test_GoogleAPISearch(unittest.TestCase):
    
    GOOGLE_API_SEARCHERS = (GAjaxSearch, GMobileSearch, GStandardSearch)
    
    def setUp(self):
        self.count = random.choice((10, 13, 15, 20, 27, 41, 50, 80))
    
    def _get_google_searchers(self, query, start, count):
        # Helper method
        searchers_instances = []
        for _class in self.GOOGLE_API_SEARCHERS:
            searchers_instances.append(_class(URL_OPEN_FUNC, query, start, count))
        return searchers_instances
        
    
    def test_len_link_results(self):
        # Len of results should be <= count
        query = "pink red blue"
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            # the length of retrieved links should be <= 'count'
            self.assertTrue(len(searcher.links) <= self.count)
    
    def test_links_results_domain(self):
        domain = "www.bonsai-sec.com"
        query = "site:%s security" % domain
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            # returned URLs' domain should be the expected
            for link in searcher.links:
                link_domain = urlParser.getDomain(link.URL)
                self.assertTrue(link_domain == domain, 
                                "Current link domain is '%s'. Expected: '%s'" % (link_domain, domain))
    
    def test_links_results_valid(self):
        # result links should be valid URLs
        query = "pink red blue"
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            for link in searcher.links:
                self.assertTrue(URL_REGEX.match(link.URL) is not None)
        
    
    def test_pages_results_type(self):
        query = "pink red blue"
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            # the returned pages should be 'httpResponse' instances
            for page in searcher.pages:
                self.assertTrue(isinstance(page, httpResponse))
    

if __name__ == "__main__":
    unittest.main()