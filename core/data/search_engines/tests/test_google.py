'''
test_google.py

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

from core.data.search_engines.google import google, \
    GAjaxSearch, GStandardSearch, GMobileSearch
from core.data.url.httpResponse import httpResponse
from core.data.url.xUrllib import xUrllib

# Global vars
HEADERS = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)'}
# TODO: This needs to be mocked up!
URL_OPENER = xUrllib()
URL_REGEX = re.compile('((http|https)://([\w:@\-\./]*?)/[^ \n\r\t"\'<>]*)', re.U)

def URL_OPEN_FUNC( url ):
    try:
        return URL_OPENER.GET(url, headers=HEADERS, cache=True, grep=False)
    except KeyboardInterrupt:
        raise Exception('Catched KeyboardInterrupt and avoided nosetests crash.')


class test_google(unittest.TestCase):
    
    def setUp(self):
        self.query, self.limit = random.choice([('big bang theory', 200),
                                                ('two and half man', 37),
                                                ('doctor house', 55)])
        self.gse = google(URL_OPENER)
        
    
    def test_get_links_results_len(self):
        # Len of results must be ge. than limit
        try:
            results = self.gse.getNResults(self.query, self.limit)
        except KeyboardInterrupt:
            raise Exception('Caught KeyboardInterrupt and avoided nosetests crash.')
        else:
            # Len of results must be le. than limit
            self.assertTrue(len(results) <= self.limit)
            
            # I want to get some results...
            self.assertTrue(len(results) >= 10, results)
            self.assertTrue(len(set([r.URL.getDomain() for r in results])) >= 3, results)
            
            # URLs should be unique
            self.assertTrue(len(results) == len(set([r.URL for r in results])))
    
    def test_page_body(self):
        # Verify that responses' body contains at least one word in query
        try:
            responses = self.gse.getNResultPages(self.query, self.limit)
        except KeyboardInterrupt:
            raise Exception('Caught KeyboardInterrupt and avoided nosetests crash.')
        else:
            words = self.query.split()
            for resp in responses:
                found = False
                html_text = resp.getBody()
                for word in words:
                    if word in html_text:
                        found = True
                        break
                self.assertTrue(found)

class BaseGoogleAPISearchTest(object):
    '''
    See below, this base class is not intended to be run by nosetests
    '''
    GOOGLE_API_SEARCHER = None
    RESULT_SIZES = (10, 13, 15, 20, 27, 41, 50, 80)
    
    def setUp(self):
        self.count = random.choice( self.RESULT_SIZES )
        
    def test_len_link_results(self):
        # Len of results should be <= count
        query = "pink red blue"
        start = 0
        searcher = self.GOOGLE_API_SEARCHER(URL_OPEN_FUNC, query, start, count)        
        
        # the length of retrieved links should be <= 'count'
        self.assertTrue(len(searcher.links) <= self.count)
        
        # The length of the retrieved links should be >= min(RESULT_SIZES),
        # this means that we got at least *some* results from Google using
        # this specific GOOGLE_API_SEARCHER
        self.assertTrue(len(searcher.links) >= min(self.RESULT_SIZES) )
    
    def test_links_results_domain(self):
        domain = "www.bonsai-sec.com"
        query = "site:%s security" % domain
        start = 0
        searcher = self.GOOGLE_API_SEARCHER(URL_OPEN_FUNC, query, start, count)
        
        for link in searcher.links:
            link_domain = link.URL.getDomain()
            self.assertTrue(link_domain == domain, 
                            "Current link domain is '%s'. Expected: '%s'" % (link_domain, domain))
    
    def test_links_results_valid(self):
        # result links should be valid URLs
        query = "pink red blue"
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            for link in searcher.links:
                self.assertTrue(URL_REGEX.match(link.URL.url_string) is not None)
        
    
    def test_pages_results_type(self):
        query = "pink red blue"
        start = 0
        for searcher in self._get_google_searchers(query, start, self.count):
            # the returned pages should be 'httpResponse' instances
            for page in searcher.pages:
                self.assertTrue(isinstance(page, httpResponse))
    
class test_GAjaxSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GOOGLE_API_SEARCHER = GAjaxSearch
    
class test_GMobileSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GOOGLE_API_SEARCHER = GMobileSearch

class test_GStandardSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GOOGLE_API_SEARCHER = GStandardSearch
    