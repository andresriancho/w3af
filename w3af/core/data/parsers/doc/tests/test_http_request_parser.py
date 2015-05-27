"""
test_http_request_parser.py

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

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.http_request_parser import (http_request_parser,
                                                            check_version_syntax,
                                                            check_uri_syntax)


class TestHttpRequestParser(unittest.TestCase):

    def test_head_post_data(self):
        request_head = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n'
        post_data = 'foo=bar'
        fr = http_request_parser(request_head, post_data)

        self.assertIsInstance(fr, FuzzableRequest)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertEqual(fr.get_data(), post_data)

    def test_qs(self):
        fr = http_request_parser('GET http://www.w3af.com/ HTTP/1.0', '')

        self.assertIsInstance(fr, FuzzableRequest)
        self.assertEqual(fr.get_method(), 'GET')
        self.assertEqual(fr.get_data(), '')

    def test_invalid_url(self):
        self.assertRaises(BaseFrameworkException,
                          http_request_parser, 'GET / HTTP/1.0', '')

    def test_invalid_protocol(self):
        self.assertRaises(BaseFrameworkException, http_request_parser,
                          'ABCDEF', '')

    def test_simple_GET(self):
        http_request = 'GET http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Foo: bar\n'

        fr = http_request_parser(http_request, '')
        exp_headers = Headers([('Host', 'www.w3af.org'), ('Foo', 'bar')])

        self.assertEquals(fr.get_headers(), exp_headers)
        self.assertEqual(fr.get_url().get_domain(), 'www.w3af.org')
        self.assertEqual(fr.get_data(), '')

    def test_simple_GET_relative(self):
        http_request = 'GET / HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Foo: bar\n'

        fr = http_request_parser(http_request, '')
        exp_headers = Headers([('Host', 'www.w3af.org'), ('Foo', 'bar')])

        self.assertEquals(fr.get_headers(), exp_headers)
        self.assertEqual(fr.get_url().get_domain(), 'www.w3af.org')
        self.assertEqual(fr.get_data(), '')

    def test_POST_repeated(self):
        request_head = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       'Foo: spam\n' \
                       'Foo: eggs\n'
        post_data = 'a=1&a=2'
        fr = http_request_parser(request_head, post_data)

        exp_headers = Headers([('Host', 'www.w3af.org'),
                               ('Content-Type',
                                'application/x-www-form-urlencoded'),
                               ('Foo', 'spam, eggs')])

        self.assertEqual(fr.get_headers(), exp_headers)
        self.assertEquals(fr.get_data(), post_data)

    def test_check_version_syntax(self):
        self.assertTrue(check_version_syntax('HTTP/1.0'))

        self.assertRaises(BaseFrameworkException, check_version_syntax, 'HTTPS/1.0')
        self.assertRaises(BaseFrameworkException, check_version_syntax, 'HTTP/1.00000000000000')
        self.assertRaises(BaseFrameworkException, check_version_syntax, 'ABCDEF')
    
    def test_check_uri_syntax(self):
        self.assertEqual(check_uri_syntax('http://abc/def.html'),
                         'http://abc/def.html')

        self.assertRaises(BaseFrameworkException, check_uri_syntax, 'ABCDEF')
