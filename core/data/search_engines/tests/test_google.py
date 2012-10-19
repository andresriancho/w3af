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

from nose.plugins.skip import SkipTest

from core.data.search_engines.google import (google, GAjaxSearch, 
                                             GStandardSearch, GMobileSearch,
                                             FINISHED_OK, IS_NEW)
from core.data.url.HTTPResponse import HTTPResponse
from core.data.url.xUrllib import xUrllib

URL_REGEX = re.compile('((http|https)://([\w:@\-\./]*?)/[^ \n\r\t"\'<>]*)', re.U)


class test_google(unittest.TestCase):
    '''
    This unittest verifies that the Google class works. Remember that this class
    internally calls GAjaxSearch, GStandardSearch, GMobileSearch in order to avoid
    being blocked by Google's anti-automation.
    
    @see: test_GMobileSearch, test_GStandardSearch, test_GAjaxSearch below for
          tests on these particular search implementations.
    '''
    def setUp(self):
        raise SkipTest('Skip for now.')
        self.query, self.limit = random.choice([('big bang theory', 200),
                                                ('two and half man', 37),
                                                ('doctor house', 55)])
        opener = xUrllib()
        self.gse = google(opener)
        
    
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
    @see: test_GMobileSearch, test_GStandardSearch, test_GAjaxSearch below for
          tests on these particular search implementations.
    
    This base class is not intended to be run by nosetests.
    '''
    GoogleApiSearcher = None
    
    COUNT = 10
        
    def test_len_link_results(self):
        keywords = ["pink", "red", "blue"]
        random.shuffle(keywords)
        query = ' '.join( keywords )
        start = 0
        searcher = self.GoogleApiSearcher(self.opener, query, start, self.COUNT)        

        self.assertEqual(searcher.status, IS_NEW)
        
        # This actually does the search
        searcher.links
        
        msg = 'This test fails randomly based on Google\'s anti automation'
        msg += ' protection, if it fails you should run it again in a couple of'
        msg += ' minutes. Many consecutive failures show that our code is NOT'
        msg += ' working anymore.'
        self.assertEqual(searcher.status, FINISHED_OK, msg)
        
        msg = 'Got less results than expected:\n%s' % '\n'.join(str(r) for r in searcher.links)
        self.assertEqual(len(searcher.links), self.COUNT, msg)
        
        for link in searcher.links:
            self.assertTrue(URL_REGEX.match(link.URL.url_string) is not None)
        
        for page in searcher.pages:
            self.assertTrue(isinstance(page, HTTPResponse))
        
        # Check that the links are related to my search
        related = 0
        for link in searcher.links:
            for key in keywords:
                if key in link.URL.url_string.lower():
                    related += 1
        
        self.assertTrue( related > 5, related)
    
    def test_links_results_domain(self):
        domain = "www.bonsai-sec.com"
        query = "site:%s" % domain
        start = 0
        searcher = self.GoogleApiSearcher(self.opener, query, start, self.COUNT)
        
        self.assertEqual(searcher.status, IS_NEW)
        
        # This actually does the search
        searcher.links
        
        msg = 'This test fails randomly based on Google\'s anti automation'
        msg += ' protection, if it fails you should run it again in a couple of'
        msg += ' minutes. Many consecutive failures show that our code is NOT'
        msg += ' working anymore.'
        self.assertEqual(searcher.status, FINISHED_OK, msg)
        
        msg = 'Got less results than expected:\n%s' % '\n'.join(str(r) for r in searcher.links)
        self.assertEqual(len(searcher.links), self.COUNT, msg)
        
        for link in searcher.links:
            link_domain = link.URL.getDomain()
            msg = "Current link domain is '%s'. Expected: '%s'" % (link_domain, domain)
            self.assertEqual(link_domain, domain,msg)
    
    

class test_GAjaxSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GoogleApiSearcher = GAjaxSearch
    
    def setUp(self):
        self.opener = xUrllib()
    

class test_GMobileSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GoogleApiSearcher = GMobileSearch

    def setUp(self):
        self.opener = xUrllib()

class test_GStandardSearch(unittest.TestCase, BaseGoogleAPISearchTest):
    GoogleApiSearcher = GStandardSearch
    
    def setUp(self):
        self.opener = xUrllib()