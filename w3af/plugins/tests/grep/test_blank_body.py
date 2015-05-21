"""
test_blank_body.py

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
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.plugins.grep.blank_body import blank_body


class test_blank_body(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = blank_body()
        self.url = URL('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_blank_body(self):
        body = ''
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('blank_body', 'blank_body')), 1)

    def test_blank_body_none(self):
        body = 'header body footer'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 0)

    def test_blank_body_method(self):
        body = ''
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        request = FuzzableRequest(self.url, method='ARGENTINA')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 0)

    def test_blank_body_code(self):
        body = ''
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(401, body, headers, self.url, self.url, _id=1)
        request = FuzzableRequest(self.url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('blank_body', 'blank_body')), 0)
