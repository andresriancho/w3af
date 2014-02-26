# -*- coding: utf-8 -*-
"""
test_cache.py

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

from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.handlers.cache import CacheHandler, SQLCachedResponse
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers


class TestCacheHandler(unittest.TestCase):
    
    def tearDown(self):
        CacheHandler().clear()
    
    def test_basic(self):
        url = URL('http://www.w3af.org')
        request = HTTPRequest(url, cache=True)
        
        cache = CacheHandler()
        self.assertEqual(cache.default_open(request), None)
        
        response = FakeHttplibHTTPResponse(200, 'OK', 'spameggs', Headers(),
                                           url.url_string)
        cache.http_response(request, response)
        
        cached_response = cache.default_open(request)
        
        self.assertIsInstance(cached_response, SQLCachedResponse)
        
        self.assertEqual(cached_response.code, response.code)
        self.assertEqual(cached_response.msg, response.msg)
        self.assertEqual(cached_response.read(), response.read())
        self.assertEqual(Headers(cached_response.info().items()), response.info())
        self.assertEqual(cached_response.geturl(), response.geturl())

    def test_no_cache(self):
        url = URL('http://www.w3af.org')
        request = HTTPRequest(url, cache=False)
        
        cache = CacheHandler()
        self.assertEqual(cache.default_open(request), None)
        
        response = FakeHttplibHTTPResponse(200, 'OK', 'spameggs', Headers(),
                                           url.url_string)
        cache.http_response(request, response)
        self.assertEqual(cache.default_open(request), None)


class FakeHttplibHTTPResponse(object):
    def __init__(self, code, msg, body, headers, url):
        self.code = code
        self.msg = msg
        self.body = body
        self.headers = headers
        self.url = url
    
    def geturl(self):
        return self.url
    
    def read(self):
        return self.body
    
    def info(self):
        return self.headers