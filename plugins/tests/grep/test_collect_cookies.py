'''
test_collect_cookies.py

Copyright 2012 Andres Riancho

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
import unittest

import core.data.kb.knowledgeBase as kb

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import url_object
from core.controllers.coreHelpers.fingerprint_404 import fingerprint_404_singleton
from plugins.grep.collect_cookies import collect_cookies


class test_collect_cookies(unittest.TestCase):
    
    def setUp(self):
        fingerprint_404_singleton( [False, False, False] )
        kb.kb.cleanup()
        self.plugin = collect_cookies()
    
    def tearDown(self):
        self.plugin.end()
        
    def test_collect_cookies_negative(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'cookies')), 0 )
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'invalid-cookies')), 0 )
    
    def test_collect_cookies_simple_cookie(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'cookies')), 1 )
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'invalid-cookies')), 0 )

    def test_collect_cookies_secure_httponly(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def; secure; HttpOnly'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'invalid-cookies')), 0 )

    def test_collect_cookies_empty(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': ''}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'cookies')), 1 )
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'invalid-cookies')), 0)

    def test_collect_cookies_fingerprint(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'PHPSESSID=d98238ab39de038'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)
        
        cookies = kb.kb.getData('collect_cookies', 'cookies')
        
        self.assertEqual( len(cookies), 2 )
        self.assertEqual( len(kb.kb.getData('collect_cookies', 'invalid-cookies')), 0)
        self.assertTrue( any([True for i in cookies if 'The remote platform is: "PHP"' in i.getDesc()]) )
