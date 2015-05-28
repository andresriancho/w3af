"""
test_private_ip.py

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
from w3af.plugins.grep.private_ip import private_ip


class test_private_ip(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        self.plugin = private_ip()
        self.url = URL('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_private_ip_empty(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'HTML')), 0)

    def test_private_ip_find(self):
        body = '<html><head>192.168.1.1</head></html>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'HTML')), 1)

    def test_private_ip_broken_html(self):
        body = '<html><head>192.168.1.1</html>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'HTML')), 1)

    def test_private_ip_find_10(self):
        body = 'header 10.2.34.2 footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'HTML')), 1)

    def test_private_ip_find_header(self):
        body = 'header content footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('x-via', '10.3.4.5')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'header')), 1)

    def test_private_ip_find_header_group(self):
        body = 'header content footer'
        headers = Headers([('content-type', 'text/html'),
                           ('x-via', '10.3.4.5')])

        url_1 = URL('http://www.w3af.com/1')
        response_1 = HTTPResponse(200, body, headers, url_1, url_1, _id=1)
        request_1 = FuzzableRequest(url_1, method='GET')
        self.plugin.grep(request_1, response_1)

        url_2 = URL('http://www.w3af.com/2')
        response_2 = HTTPResponse(200, body, headers, url_2, url_2, _id=2)
        request_2 = FuzzableRequest(url_2, method='GET')
        self.plugin.grep(request_2, response_2)

        info_sets = kb.kb.get('private_ip', 'header')
        self.assertEquals(len(info_sets), 1)

        info_set = info_sets[0]
        expected_desc = 'A total of 2 HTTP responses contained the private IP' \
                        ' address 10.3.4.5 in the "x-via" response header. The' \
                        ' first ten matching URLs are:\n' \
                        ' - http://www.w3af.com/2\n' \
                        ' - http://www.w3af.com/1\n'
        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(info_set.get_desc(), expected_desc)

    def test_private_ip_find_header_no_group(self):
        body = 'header content footer'

        url_1 = URL('http://www.w3af.com/1')
        headers_1 = Headers([('content-type', 'text/html'),
                             ('x-via', '10.3.4.5')])
        response_1 = HTTPResponse(200, body, headers_1, url_1, url_1, _id=1)
        request_1 = FuzzableRequest(url_1, method='GET')
        self.plugin.grep(request_1, response_1)

        url_2 = URL('http://www.w3af.com/2')
        headers_2 = Headers([('content-type', 'text/html'),
                             ('x-via', '10.6.6.6')]) # Changed the ip address
        response_2 = HTTPResponse(200, body, headers_2, url_2, url_2, _id=2)
        request_2 = FuzzableRequest(url_2, method='GET')
        self.plugin.grep(request_2, response_2)

        info_sets = kb.kb.get('private_ip', 'header')
        self.assertEquals(len(info_sets), 2)

    def test_private_ip_no(self):
        body = '<script> 1010.2.3.4 </script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('x-via', '10.256.3.10.1.2.3')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('private_ip', 'HTML')), 0)
        self.assertEquals(len(kb.kb.get('private_ip', 'header')), 0)
