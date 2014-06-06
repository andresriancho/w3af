"""
test_create_cookie.py

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

from w3af.core.data.request.factory import _create_cookie
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.headers import Headers


class TestCreateCookie(unittest.TestCase):
    def test_create_cookie(self):
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'), ('Cookie', 'abc=def')])
        response = HTTPResponse(200, '', headers, url, url)

        cookie = _create_cookie(response)

        self.assertEqual(cookie, Cookie('abc=def'))
