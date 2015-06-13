"""
test_google.py

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
import random
import re
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.search_engines.google import (google, GAjaxSearch,
                                                  GStandardSearch,
                                                  GMobileSearch,
                                                  FINISHED_OK, IS_NEW)

GOOGLE_MSG = ('This test fails randomly based on Google\'s anti automation'
              ' protection, if it fails you should run it again in a couple of'
              ' minutes. Many consecutive failures show that our code is NOT'
              ' working anymore.')
URL_REGEX = re.compile('((http|ftp|https)://([\w:@\-\./]*?)/[^ \n\r\t"\'<>]*)',
                       re.U)


@attr('internet')
@attr('fails')
class TestGoogle(unittest.TestCase):
    """
    This unittest verifies that the Google class works. Remember that this class
    internally calls GAjaxSearch, GStandardSearch, GMobileSearch in order to
    avoid being blocked by Google's anti-automation.

    @see: test_GMobileSearch, test_GStandardSearch, test_GAjaxSearch below for
          tests on these particular search implementations.
    """
    def setUp(self):
        self.query, self.limit = random.choice([('big bang theory', 20),
                                                ('two and half man', 20),
                                                ('doctor house', 20)])
        opener = ExtendedUrllib()
        self.gse = google(opener)

    def test_get_links_results_len(self):
        results = self.gse.get_n_results(self.query, self.limit)

        self.assertEqual(len(results), self.limit)

        # Results need to be from at least three different domains, this is an
        # easy way to verify that the REGEX is working as expected
        self.assertTrue(
            len(set([r.URL.get_domain() for r in results])) >= 3, results)

        # URLs should be unique
        self.assertTrue(len(results) == len(set([r.URL for r in results])))

    def test_page_body(self):
        responses = self.gse.get_n_result_pages(self.query, self.limit)

        #
        # Verify that responses' body contains at least one word in query
        #
        words = self.query.split()

        for resp in responses:
            found = False
            html_text = resp.get_body()
            for word in words:
                if word in html_text:
                    found = True
                    break
            self.assertTrue(found)


class BaseGoogleAPISearch(unittest.TestCase):
    """
    @see: test_GMobileSearch, test_GStandardSearch, test_GAjaxSearch below for
          tests on these particular search implementations.

    This base class is not intended to be run by nosetests.
    """
    GoogleApiSearcher = None

    COUNT = 10
    
    def setUp(self):
        self.opener = ExtendedUrllib()

    def tearDown(self):
        self.opener.end()

    @attr('fails')
    def test_len_link_results(self):
        if self.GoogleApiSearcher is None:
            return
        
        keywords = ['pink', 'red', 'blue']
        random.shuffle(keywords)
        query = ' '.join(keywords)
        start = 0
        # pylint: disable=E1102
        # E1102: self.GoogleApiSearcher is not callable
        searcher = self.GoogleApiSearcher(self.opener, query, start, self.COUNT)

        self.assertEqual(searcher.status, IS_NEW)

        # This actually does the search
        searcher.links

        self.assertEqual(searcher.status, FINISHED_OK, GOOGLE_MSG)

        link_list = '\n'.join(str(r) for r in searcher.links)
        msg = 'Got less results than expected, %s is less than %s:\n%s'
        msg = msg % (len(searcher.links), self.COUNT, link_list)
        self.assertGreaterEqual(len(searcher.links), self.COUNT, msg)

        for link in searcher.links:
            self.assertTrue(URL_REGEX.match(link.URL.url_string) is not None,
                            link.URL.url_string)

        for page in searcher.pages:
            self.assertTrue(isinstance(page, HTTPResponse))

        # Check that the links are related to my search
        related = 0
        for link in searcher.links:
            for key in keywords:
                if key in link.URL.url_string.lower():
                    related += 1

        self.assertTrue(related > 5, related)

    @attr('fails')
    def test_links_results_domain(self):
        if self.GoogleApiSearcher is None:
            return
        
        domain = "www.bonsai-sec.com"
        query = "site:%s" % domain
        start = 0
        # pylint: disable=E1102
        # E1102: self.GoogleApiSearcher is not callable
        searcher = self.GoogleApiSearcher(self.opener, query, start, self.COUNT)

        self.assertEqual(searcher.status, IS_NEW)

        # This actually does the search
        searcher.links

        self.assertEqual(searcher.status, FINISHED_OK, GOOGLE_MSG)

        msg = 'Got less results than expected:\n%s' % '\n'.join(
            str(r) for r in searcher.links)
        self.assertEqual(len(searcher.links), self.COUNT, msg)

        for link in searcher.links:
            link_domain = link.URL.get_domain()
            msg = "Current link domain is '%s'. Expected: '%s'" % (
                link_domain, domain)
            self.assertEqual(link_domain, domain, msg)


@attr('internet')
@attr('fails')
class TestGAjaxSearch(BaseGoogleAPISearch):
    GoogleApiSearcher = GAjaxSearch


@attr('internet')
@attr('fails')
class TestGMobileSearch(BaseGoogleAPISearch):
    GoogleApiSearcher = GMobileSearch


@attr('internet')
@attr('fails')
class TestGStandardSearch(BaseGoogleAPISearch):
    GoogleApiSearcher = GStandardSearch
