"""
test_http_auth_detect.py

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
from w3af.plugins.grep.http_auth_detect import http_auth_detect


class test_http_auth_detect(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')
        self.headers = Headers({'content-type': 'text/html'}.items())
        self.request = FuzzableRequest(self.url, method='GET')
        self.plugin = http_auth_detect()
        kb.kb.cleanup()

    def tearDown(self):
        self.plugin.end()

    def test_http_auth_detect_negative(self):
        response = HTTPResponse(200, '', self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'auth')), 0)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'userPassUri')), 0)

    def test_http_auth_detect_negative_long(self):
        body = 'ABC ' * 10000
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'auth')), 0)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'userPassUri')), 0)

    def test_http_auth_detect_uri(self):
        body = 'ABC ' * 100
        body += '<a href="http://abc:def@www.w3af.com/foo.bar">test</a>'
        body += '</br> ' * 50
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'auth')), 0)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'userPassUri')), 1)

    def test_http_auth_detect_non_rfc(self):
        body = ''
        response = HTTPResponse(401, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(
            len(kb.kb.get('http_auth_detect', 'non_rfc_auth')), 1)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'userPassUri')), 0)

    def test_http_auth_detect_simple(self):
        body = ''
        hdrs = {'content-type': 'text/html', 'www-authenticate': 'realm-w3af'}
        hdrs = Headers(hdrs.items())
        response = HTTPResponse(401, body, hdrs, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'auth')), 1)
        self.assertEqual(len(kb.kb.get('http_auth_detect', 'userPassUri')), 0)
