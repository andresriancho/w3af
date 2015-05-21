"""
test_file_upload.py

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
from w3af.plugins.grep.file_upload import file_upload
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class test_file_upload(unittest.TestCase):

    def setUp(self):
        self.plugin = file_upload()
        kb.kb.clear('file_upload', 'file_upload')

    def tearDown(self):
        self.plugin.end()

    def test_simple(self):
        body = 'header <form><input type="file"></form> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('file_upload', 'file_upload')), 1)
        i = kb.kb.get('file_upload', 'file_upload')[0]
        self.assertEquals(i.get_name(), 'File upload form')

    def test_complex(self):
        body = 'header <form><Input type="File"></form> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('file_upload', 'file_upload')), 1)
        i = kb.kb.get('file_upload', 'file_upload')[0]
        self.assertEquals(i.get_name(), 'File upload form')

    def test_none(self):
        body = 'header <form><noinput type="file"></form> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('file_upload', 'file_upload')), 0)
