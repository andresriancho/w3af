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

from w3af.core.data.parsers.parser_cache import ParserCache
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers


class TestParserCache(unittest.TestCase):
    
    def setUp(self):
        self.url = URL('http://w3af.com')
        self.headers = Headers([(u'content-type', u'text/html')])
        self.dpc = ParserCache()
        
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
        all_chars = ''.join([chr(i) for i in xrange(0,255)])
        response = HTTPResponse(200, all_chars, self.headers, self.url, self.url)
        parser = self.dpc.get_document_parser_for(response)
