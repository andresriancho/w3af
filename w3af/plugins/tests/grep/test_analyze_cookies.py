"""
test_analyze_cookies.py

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

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.plugins.grep.analyze_cookies import analyze_cookies


class TestAnalyzeCookies(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        self.plugin = analyze_cookies()

    def tearDown(self):
        self.plugin.end()

    def test_analyze_cookies_negative(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 0)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_simple_cookie(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_collect(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers(
            {'content-type': 'text/html', 'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        headers = Headers(
            {'content-type': 'text/html', 'Set-Cookie': '123=456'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 2)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_collect_uniq(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': '123=456'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=456'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 2)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_secure_httponly(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure; HttpOnly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_empty(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers(
            {'content-type': 'text/html', 'Set-Cookie': ''}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_fingerprint(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'PHPSESSID=d98238ab39de038'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        security = kb.kb.get('analyze_cookies', 'security')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(security), 2)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        self.assertTrue(any([True for i in security if 'The remote platform is: "PHP"' in i.get_desc()]))

    def test_analyze_cookies_secure_over_http(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        security = kb.kb.get('analyze_cookies', 'security')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(security), 2)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        self.assertTrue(any([True for i in security if 'A cookie marked with the secure flag' in i.get_desc()]))

    def test_analyze_cookies_no_httponly(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        security = kb.kb.get('analyze_cookies', 'security')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(security), 1)
        self.assertEqual(
            len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        self.assertTrue(any([True for i in security if 'A cookie without the HttpOnly flag' in i.get_desc()]))

    def test_analyze_cookies_with_httponly(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure; httponly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_case_sensitive(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def;Secure;HttpOnly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_secure(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def;HttpOnly;  secure;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_with_httponly_case_sensitive_expires(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = {'content-type': 'text/html',
                   'Set-Cookie': 'name2=value2; Expires=Wed, 09-Jun-2021 10:18:14 GMT;Secure;HttpOnly'}
        headers = Headers(headers.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_https_value_over_http(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=defjkluio; secure; httponly;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        # Receive the cookie over HTTPS
        self.plugin.grep(request, response)

        url = URL('http://www.w3af.com/?id=defjkluio')
        headers = Headers({'content-type': 'text/html'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        # Send the cookie over HTTP as a parameter value
        self.plugin.grep(request, response)

        security = kb.kb.get('analyze_cookies', 'security')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(security), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        
        names = [i.get_name() for i in security]
        self.assertIn('Secure cookies over insecure channel', names)