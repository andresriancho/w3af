"""
test_strange_headers.py

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
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.strange_headers import strange_headers


class test_strange_headers(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = strange_headers()

    def tearDown(self):
        self.plugin.end()

    def test_strange_headers_positive(self):
        body = 'Hello world'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('hello-world', 'yes!')])
        request = FuzzableRequest(url, method='GET')

        resp_positive = HTTPResponse(200, body, headers, url, url, _id=1)
        self.plugin.grep(request, resp_positive)

        infos = kb.kb.get('strange_headers', 'strange_headers')
        self.assertEquals(len(infos), 1)

        info = infos[0]
        self.assertEqual(info.get_name(), 'Strange header')
        self.assertEqual(info.get_url(), url)

    def test_strange_headers_negative(self):
        body = 'Hello world'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('x-pad', 'yes!')])
        request = FuzzableRequest(url, method='GET')

        resp_positive = HTTPResponse(200, body, headers, url, url, _id=1)
        self.plugin.grep(request, resp_positive)

        infos = kb.kb.get('strange_headers', 'strange_headers')
        self.assertEquals(len(infos), 0)
