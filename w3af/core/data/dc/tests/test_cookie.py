# -*- coding: utf-8 -*-
"""
test_cookie.py

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
import copy

from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse


class TestCookieDc(unittest.TestCase):
    
    def test_basic(self):
        cookie_obj = Cookie('test=123; foobar=abc def; path=/')
        
        self.assertIn('test', cookie_obj)
        self.assertIn('foobar', cookie_obj)
        self.assertIn('path', cookie_obj)

        self.assertEqual(cookie_obj['test'], ['123'])
        self.assertEqual(cookie_obj['foobar'], ['abc def'])
        
    def test_repeated(self):
        cookie_obj = Cookie('test=123; test=abc def; path=/')
        
        self.assertIn('test', cookie_obj)
        self.assertIn('path', cookie_obj)
        
        self.assertEqual(cookie_obj['test'], ['123', 'abc def'])

    def test_create_cookie(self):
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'), ('Cookie', 'abc=def')])
        response = HTTPResponse(200, '', headers, url, url)

        cookie = Cookie.from_http_response(response)

        self.assertEqual(cookie, Cookie('abc=def'))

    def test_copy_with_token(self):
        dc = Cookie('one=123; two=567; path=/')

        dc.set_token(('one', 0))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())
        self.assertEqual(dc_copy.get_token().get_name(), 'one')