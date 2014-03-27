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

from w3af.core.data.dc.cookie import Cookie


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
        
        