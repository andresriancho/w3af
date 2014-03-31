"""
test_code_disclosure.py

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

from itertools import repeat
from mock import patch

import w3af.core.data.kb.knowledge_base as kb

from w3af.plugins.grep.code_disclosure import code_disclosure
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL


class test_code_disclosure(unittest.TestCase):

    def setUp(self):
        self.plugin = code_disclosure()
        kb.kb.clear('code_disclosure', 'code_disclosure')

    def tearDown(self):
        self.plugin.end()

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_ASP_code_disclosure(self, *args):
        body = 'header <% Response.Write("Hello World!") %> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 1)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_PHP_code_disclosure(self, *args):
        body = 'header <? echo $a; ?> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 1)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_code_disclosure_blank(self, *args):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 0)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_code_disclosure(self, *args):
        body = """Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Integer
        eu lacus accumsan arcu fermentum euismod. Donec pulvinar porttitor
        tellus. Aliquam venenatis. Donec facilisis pharetra tortor.  In nec
        mauris eget magna consequat convallis. Nam sed sem vitae odio
        pellentesque interdum. Sed consequat viverra nisl. Suspendisse arcu
        metus, blandit quis, rhoncus <a>,</a> pharetra eget, velit. Mauris
        urna. Morbi nonummy molestie orci. Praesent nisi elit, fringilla ac,
        suscipit non, tristique vel, ma<?uris. Curabitur vel lorem id nisl porta
        adipiscing. Suspendisse eu lectus. In nunc. Duis vulputate tristique
        enim. Donec quis lectus a justo imperdiet tempus."""

        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 0)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_code_disclosure_xml(self, *args):
        body = """
                <?xml version="1.0"?>
                <note>
                    <to>Tove</to>
                    <from>Jani</from>
                    <heading>Reminder</heading>
                    <body>Don't forget me this weekend!</body>
                </note>"""
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 0)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_analysis_content_type(self, *args):
        body = 'header <? echo $a; ?> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'image/jpeg')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('code_disclosure', 'code_disclosure')), 0)
