"""
test_parser_cache.py

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

from mock import patch, PropertyMock

from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.tests.test_document_parser import _build_http_response
from w3af.core.data.parsers.parser_cache import ParserCache
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.tests.test_mp_document_parser import DelayedParser
from w3af.core.data.parsers.utils.response_uniq_id import get_response_unique_id
from w3af.core.controllers.exceptions import BaseFrameworkException


class TestParserCache(unittest.TestCase):
    
    def setUp(self):
        self.url = URL('http://w3af.com')
        self.headers = Headers([(u'content-type', u'text/html')])
        self.dpc = ParserCache()

    def tearDown(self):
        self.dpc.clear()

    def test_basic(self):
        resp1 = HTTPResponse(200, 'abc', self.headers, self.url, self.url)         
        resp2 = HTTPResponse(200, 'abc', self.headers, self.url, self.url)
        
        parser1 = self.dpc.get_document_parser_for(resp1)
        parser2 = self.dpc.get_document_parser_for(resp2)
        
        self.assertEqual(id(parser1), id(parser2))
    
    def test_bug_13_Dec_2012(self):
        url1 = URL('http://w3af.com/foo/')
        url2 = URL('http://w3af.com/bar/')
        body = '<a href="?id=1">1</a>'
        resp1 = HTTPResponse(200, body, self.headers, url1, url1)         
        resp2 = HTTPResponse(200, body, self.headers, url2, url2)
        
        parser1 = self.dpc.get_document_parser_for(resp1)
        parser2 = self.dpc.get_document_parser_for(resp2)
        
        self.assertNotEqual(id(parser1), id(parser2))
        
        _, parsed_refs_1 = parser1.get_references()
        _, parsed_refs_2 = parser2.get_references()
        
        self.assertEqual(parsed_refs_1, parsed_refs_2)
    
    def test_issue_188_invalid_url(self):
        # https://github.com/andresriancho/w3af/issues/188
        all_chars = ''.join([chr(i) for i in xrange(0, 255)])
        response = HTTPResponse(200, all_chars, self.headers, self.url, self.url)
        self.dpc.get_document_parser_for(response)

    def test_cache_blacklist_after_timeout(self):
        #
        # If the cache tries to parse an HTTP response, that process fails, then we blacklist
        # the HTTP response so it never gets parsed again.
        #
        mmpdp = 'w3af.core.data.parsers.mp_document_parser.%s'
        kmpdp = mmpdp % 'MultiProcessingDocumentParser.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(kmpdp % 'PARSER_TIMEOUT', new_callable=PropertyMock) as timeout_mock, \
             patch(kmpdp % 'MAX_WORKERS', new_callable=PropertyMock) as max_workers_mock, \
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            #
            # Trigger the timeout
            #
            html = '<html>DelayedParser!</html>'
            http_resp = _build_http_response(html, u'text/html')

            timeout_mock.return_value = 1
            max_workers_mock.return_value = 1
            parsers_mock.return_value = [DelayedParser, HTMLParser]

            try:
                self.dpc.get_document_parser_for(http_resp)
            except BaseFrameworkException, bfe:
                self._is_timeout_exception_message(bfe, http_resp)
            else:
                self.assertTrue(False)

            #
            # Make sure it is in the blacklist
            #
            hash_string = get_response_unique_id(http_resp)
            self.assertIn(hash_string, self.dpc._parser_blacklist)

            #
            # Make sure the blacklist is used
            #
            try:
                self.dpc.get_document_parser_for(http_resp)
            except BaseFrameworkException, bfe:
                self.assertIn('Exceeded timeout while parsing', str(bfe))

    def _is_timeout_exception_message(self, toe, http_resp):
        msg = 'Reached timeout parsing "http://w3af.com/".'
        self.assertEquals(str(toe), msg)

    def test_get_tags_by_filter_simple(self):
        html = '<a href="/def">abc</a>'
        resp1 = HTTPResponse(200, html, self.headers, self.url, self.url)
        resp2 = HTTPResponse(200, html, self.headers, self.url, self.url)

        parser1 = self.dpc.get_tags_by_filter(resp1, tags=('a',))
        parser2 = self.dpc.get_tags_by_filter(resp2, tags=('a',))

        self.assertEqual(id(parser1), id(parser2))

    def test_get_tags_by_filter_different_tags(self):
        html = '<a href="/def">abc</a><b>hello</b>'
        resp1 = HTTPResponse(200, html, self.headers, self.url, self.url)
        resp2 = HTTPResponse(200, html, self.headers, self.url, self.url)

        parser1 = self.dpc.get_tags_by_filter(resp1, tags=('a',))
        parser2 = self.dpc.get_tags_by_filter(resp2, tags=('b',))

        self.assertNotEqual(id(parser1), id(parser2))
