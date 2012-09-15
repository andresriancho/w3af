'''
test_analyze_cookies.py

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
from core.data.request.fuzzable_request import fuzzable_request
from core.data.parsers.urlParser import url_object
from core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
from plugins.grep.analyze_cookies import analyze_cookies


class test_analyze_cookies(unittest.TestCase):
    
    def setUp(self):
        fingerprint_404_singleton( [False, False, False] )
        kb.kb.cleanup()
        self.plugin = analyze_cookies()
    
    def tearDown(self):
        self.plugin.end()
        
    def test_analyze_cookies_negative(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 0 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )
    
    def test_analyze_cookies_simple_cookie(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )

    def test_analyze_cookies_collect(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        
        headers = {'content-type': 'text/html', 'Set-Cookie': '123=456'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 2 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )

    def test_analyze_cookies_collect_uniq(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        
        headers = {'content-type': 'text/html', 'Set-Cookie': '123=456'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=456'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 2 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )

    def test_analyze_cookies_secure_httponly(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def; secure; HttpOnly'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )

    def test_analyze_cookies_empty(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': ''}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_fingerprint(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'PHPSESSID=d98238ab39de038'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')

        self.plugin.grep(request, response)
        
        security = kb.kb.get('analyze_cookies', 'security')
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1 )
        self.assertEqual( len(security), 2 )
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        self.assertTrue( any([True for i in security if 'The remote platform is: "PHP"' in i.getDesc()]) )

    def test_analyze_cookies_secure_over_http(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def; secure;'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        security = kb.kb.get('analyze_cookies', 'security')
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(security), 2)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )
        self.assertTrue( any([True for i in security if 'A cookie marked with the secure flag' in i.getDesc()]) )

    def test_analyze_cookies_no_httponly(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        security = kb.kb.get('analyze_cookies', 'security')
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(security), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0 )
        self.assertTrue( any([True for i in security if 'A cookie without the HttpOnly flag' in i.getDesc()]) )

    def test_analyze_cookies_with_httponly(self):
        body = ''
        url = url_object('https://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def; secure; httponly'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_case_sensitive(self):
        body = ''
        url = url_object('https://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def;Secure;HttpOnly'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_secure(self):
        body = ''
        url = url_object('https://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'abc=def;HttpOnly;  secure;'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_case_sensitive_expires(self):
        body = ''
        url = url_object('https://www.w3af.com/')
        headers = {'content-type': 'text/html', 'Set-Cookie': 'name2=value2; Expires=Wed, 09-Jun-2021 10:18:14 GMT;Secure;HttpOnly'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        
        self.plugin.grep(request, response)
        
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual( len(kb.kb.get('analyze_cookies', 'security')), 0)

