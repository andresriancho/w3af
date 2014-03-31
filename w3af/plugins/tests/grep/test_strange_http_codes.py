"""
test_strange_http_codes.py

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

from w3af.plugins.grep.strange_http_codes import strange_http_codes


class test_strange_http_codes(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.plugin = strange_http_codes()

    def tearDown(self):
        self.plugin.end()

    def test_strange_http_codes(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')

        resp_200 = HTTPResponse(200, body, headers, url, url, _id=1)
        resp_404 = HTTPResponse(404, body, headers, url, url, _id=1)
        KNOWN_GOOD = [resp_200, resp_404]

        resp_999 = HTTPResponse(999, body, headers, url, url, _id=1)
        resp_123 = HTTPResponse(123, body, headers, url, url, _id=1)
        resp_567 = HTTPResponse(567, body, headers, url, url, _id=1)
        resp_666 = HTTPResponse(666, body, headers, url, url, _id=1)
        resp_777 = HTTPResponse(777, body, headers, url, url, _id=1)
        KNOWN_BAD = [resp_999, resp_123, resp_567, resp_666, resp_777]

        for resp in KNOWN_GOOD:
            kb.kb.cleanup()
            self.plugin.grep(request, resp)
            self.assertEquals(len(kb.kb.get('strange_http_codes',
                                            'strange_http_codes')), 0)

        for resp in KNOWN_BAD:
            kb.kb.cleanup()
            self.plugin.grep(request, resp)
            self.assertEquals(len(kb.kb.get('strange_http_codes',
                                            'strange_http_codes')), 1)
