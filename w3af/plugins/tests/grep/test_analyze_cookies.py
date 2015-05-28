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
from w3af.core.data.parsers.doc.url import URL
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
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_simple_cookie(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_collect_no_group(self):
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

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 2)

    def test_analyze_cookies_collect_one(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        cookie_infosets = kb.kb.get('analyze_cookies', 'cookies')
        self.assertEqual(len(cookie_infosets), 1)

        expected_desc = u'The application sent the "abc" cookie in 1 ' \
                        u'different URLs. The first ten URLs are:\n' \
                        u' - http://www.w3af.com/\n'
        info_set = cookie_infosets[0]
        self.assertEqual(len(info_set.infos), 1)
        self.assertEqual(info_set.get_desc(), expected_desc)

    def test_analyze_cookies_collect_group_by_key(self):
        body = ''
        url_1 = URL('http://www.w3af.com/1')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url_1, url_1, _id=1)
        request = FuzzableRequest(url_1, method='GET')
        self.plugin.grep(request, response)

        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=456'}.items())
        url_2 = URL('http://www.w3af.com/2')
        response = HTTPResponse(200, body, headers, url_2, url_2, _id=1)
        request = FuzzableRequest(url_2, method='GET')
        self.plugin.grep(request, response)

        cookie_infosets = kb.kb.get('analyze_cookies', 'cookies')
        self.assertEqual(len(cookie_infosets), 1)

        expected_desc = u'The application sent the "abc" cookie in 2' \
                        u' different URLs. The first ten URLs are:\n' \
                        u' - http://www.w3af.com/2\n - http://www.w3af.com/1\n'
        info_set = cookie_infosets[0]
        self.assertEqual(len(info_set.infos), 2)
        self.assertEqual(info_set.get_desc(), expected_desc)

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
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_secure_httponly(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure; HttpOnly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_empty(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': ''}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

    def test_analyze_cookies_fingerprint(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'PHPSESSID=d98238ab39de038'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        fingerprint = kb.kb.get('analyze_cookies', 'fingerprint')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(fingerprint), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        msg = 'The remote platform is: "PHP"'
        self.assertTrue(any([True for i in fingerprint if msg in i.get_desc()]))

    def test_analyze_cookies_secure_over_http(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        false_secure = kb.kb.get('analyze_cookies', 'false_secure')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(false_secure), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        msg = 'A cookie marked with the secure flag'
        self.assertTrue(any([True for i in false_secure if msg in i.get_desc()]))

    def test_analyze_cookies_no_httponly(self):
        body = ''
        url = URL('http://www.w3af.com/1')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        url = URL('http://www.w3af.com/2')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=2)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        http_only = kb.kb.get('analyze_cookies', 'http_only')

        self.assertEqual(len(http_only), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)

        info_set = http_only[0]
        expected_desc = u'The application sent the "abc" cookie without the' \
                        u' HttpOnly flag in 2 different responses. The' \
                        u' HttpOnly flag prevents potential intruders from' \
                        u' accessing the cookie value through Cross-Site' \
                        u' Scripting attacks. The first ten URLs which sent' \
                        u' the insecure cookie are:\n' \
                        u' - http://www.w3af.com/2\n - http://www.w3af.com/1\n'
        self.assertEqual(info_set.get_desc(), expected_desc)
        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(len(info_set.infos), 2)

    def test_analyze_cookies_with_httponly(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; secure; httponly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'http_only')), 0)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'secure')), 0)

    def test_analyze_cookies_with_httponly_case_sensitive(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def;Secure;HttpOnly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'http_only')), 0)

    def test_analyze_cookies_with_httponly_secure(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def;HttpOnly;  secure;'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'http_only')), 0)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'secure')), 0)

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
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'http_only')), 0)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'secure')), 0)

    def test_analyze_cookies_https_value_over_http(self):
        body = ''
        url = URL('https://www.w3af.com/')
        c = 'abc=foobarspam; secure; httponly;'
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': c}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        # Receive the cookie over HTTPS
        self.plugin.grep(request, response)

        url = URL('http://www.w3af.com/?id=foobarspam')
        headers = Headers({'content-type': 'text/html'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        # Send the cookie over HTTP as a parameter value
        self.plugin.grep(request, response)

        secure_via_http = kb.kb.get('analyze_cookies', 'secure_via_http')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(secure_via_http), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'invalid-cookies')), 0)
        
        names = [i.get_name() for i in secure_via_http]
        self.assertIn('Secure cookies over insecure channel', names)

    def test_analyze_ssl_cookie_without_secure_flag(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers({'content-type': 'text/html',
                           'Set-Cookie': 'abc=def; httponly'}.items())
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        self.plugin.grep(request, response)

        secure_info_sets = kb.kb.get('analyze_cookies', 'secure')

        self.assertEqual(len(kb.kb.get('analyze_cookies', 'cookies')), 1)
        self.assertEqual(len(kb.kb.get('analyze_cookies', 'http_only')), 0)
        self.assertEqual(len(secure_info_sets), 1)

        info_set = secure_info_sets[0]
        expected_desc = u'The application sent the "abc" cookie without the' \
                        u' Secure flag set in 1 different URLs. The Secure ' \
                        u'flag prevents the browser from sending cookies ' \
                        u'over insecure HTTP connections, thus preventing' \
                        u' potential session hijacking attacks. The first' \
                        u' ten URLs which sent the insecure cookie are:\n' \
                        u' - https://www.w3af.com/\n'
        self.assertEqual(len(info_set.infos), 1)
        self.assertEqual(info_set.get_id(), [1])
        self.assertEqual(info_set.get_desc(), expected_desc)