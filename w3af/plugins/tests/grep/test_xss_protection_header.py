"""
test_xss_protection_header.py

Copyright 2011 Andres Riancho

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

from w3af.plugins.grep.xss_protection_header import xss_protection_header
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL


class test_xss_protection_header(unittest.TestCase):

    def setUp(self):
        self.plugin = xss_protection_header()
        kb.kb.clear('xss_protection_header', 'xss_protection_header')

    def tearDown(self):
        self.plugin.end()

    def test_no_xss_protection_header(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(
            kb.kb.get('xss_protection_header', 'xss_protection_header')), 0)

    def test_xss_protection_header_enable(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', '1')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(
            kb.kb.get('xss_protection_header', 'xss_protection_header')), 0)

    def test_xss_protection_header_disable(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', '0')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(
            kb.kb.get('xss_protection_header', 'xss_protection_header')), 1)

    def test_xss_protection_header_invalid(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', 'abc' * 45)])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(
            kb.kb.get('xss_protection_header', 'xss_protection_header')), 0)
