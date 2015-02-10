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
import copy
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
        self.assertEqual(len(security), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        msg = 'The remote platform is: "PHP"'
        self.assertTrue(any([True for i in security if msg in i.get_desc()]))

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
        self.assertEqual(len(security), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        msg = 'Cookie "abc" marked with the secure flag'
        has_msg = [True for i in security if msg in i.get_desc()]
        self.assertTrue(any(has_msg))

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
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        msg = 'Cookie "abc" without the HttpOnly flag'
        has_msg = [True for i in security if msg in i.get_desc()]
        self.assertTrue(any(has_msg))

    def test_analyze_cookies_with_httponly(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'a1b2c=def; secure; httponly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_no_secure_over_https_has_cookie_name(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; httponly;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)
        security = kb.kb.get('analyze_cookies', 'security')
        name = 'Cookie "abc"'
        has_name = [True for i in security if name in i.get_desc()]
        self.assertTrue(any(has_name))
        self.assertEqual(len(security), 1)

    def test_analyze_cookies_secure_over_http_has_cookie_name(self):
        body = ''
        urls = [URL('http://www.w3af.com/a'), URL('http://www.w3af.com/b')]
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure; httponly;'}.items())

        # Make requests to multiple URLs to test that vulnerability
        # description is printed only once per cookie
        for url in urls:
            response = HTTPResponse(200, body, headers, url, url, _id=1)
            request = FuzzableRequest(url, method='GET')
            self.plugin.grep(request, response)

        security = kb.kb.get('analyze_cookies', 'security')
        name = 'Cookie "abc"'
        has_name = [True for i in security if name in i.get_desc()]
        self.assertTrue(any(has_name))
        self.assertEqual(len(security), 1)

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
        c = 'name2=value2; Expires=Wed, 09-Jun-2021 10:18:14 GMT;Secure;HttpOnly'
        headers = {'content-type': 'text/html',
                   'Set-Cookie': c}
        headers = Headers(headers.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 0)

    def test_analyze_cookies_https_value_over_http(self):
        body = ''
        url = URL('https://www.w3af.com/')
        c = 'abc=defjkluio; secure; httponly;'
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': c}.items())
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
        cname = 'with cookie: abc'
        has_cname = [True for i in security if cname in i.get_desc()]

        self.assertIn('Secure cookies over insecure channel', names)
        self.assertTrue(any(has_cname))

    def test_multiple_cookies(self):
        body = ''
        url = URL('https://www.w3af.com/')
        header_content = 'name="adf"; , name2="adfff"; secure'
        headers = Headers({'content-type': 'text/html', 
                            'Set-Cookie:' : '%s;' % header_content}.items())

        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        for hc in header_content:
            self.assertIn(hc, response.headers.values()[0])

    def test_update_without_httponly(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                            'Set-Cookie': 'name="adf"'}.items())

        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        for i in range(0,2):
            self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'security')), 1)