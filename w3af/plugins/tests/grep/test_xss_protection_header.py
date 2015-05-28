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
from w3af.core.data.parsers.doc.url import URL


class TestXSSProtectionHeader(unittest.TestCase):

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
        self.assertEqual(len(kb.kb.get('xss_protection_header',
                                       'xss_protection_header')), 0)

    def test_xss_protection_header_enable(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', '1')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('xss_protection_header',
                                       'xss_protection_header')), 0)

    def test_xss_protection_header_disable(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', '0')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('xss_protection_header',
                                       'xss_protection_header')), 1)

    def test_xss_protection_header_invalid(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', 'abc' * 45)])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('xss_protection_header',
                                       'xss_protection_header')), 0)

    def test_xss_protection_header_disable_group(self):
        body = ''
        headers = Headers([('content-type', 'text/html'),
                           ('X-XSS-Protection', '0')])

        url_1 = URL('http://www.w3af.com/1')
        response_1 = HTTPResponse(200, body, headers, url_1, url_1, _id=1)
        request_1 = FuzzableRequest(url_1, method='GET')
        self.plugin.grep(request_1, response_1)

        url_2 = URL('http://www.w3af.com/2')
        response_2 = HTTPResponse(200, body, headers, url_2, url_2, _id=3)
        request_2 = FuzzableRequest(url_2, method='GET')
        self.plugin.grep(request_2, response_2)

        info_sets = kb.kb.get('xss_protection_header', 'xss_protection_header')
        self.assertEqual(len(info_sets), 1)

        expected_desc = u'The remote web server sent 2 HTTP responses with' \
                        u' the X-XSS-Protection header with a value of "0",' \
                        u' which disables Internet Explorer\'s XSS filter.' \
                        u' The first ten URLs which sent the insecure header' \
                        u' are:\n - http://www.w3af.com/2\n' \
                        u' - http://www.w3af.com/1\n'

        info_set = info_sets[0]
        self.assertEqual(info_set.get_id(), [1, 3])
        self.assertEqual(info_set.get_desc(), expected_desc)
