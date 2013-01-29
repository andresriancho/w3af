'''
test_cookie_handler.py

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

'''
import unittest
import urllib2

from core.data.url.handlers.cookie_handler import CookieHandler
from core.data.url.HTTPRequest import HTTPRequest
from core.data.parsers.url import URL
from core.data.url.extended_urllib import ExtendedUrllib


class TestCookieHandler(unittest.TestCase):

    URL_SENDS_COOKIE = URL(
        'http://moth/w3af/core/cookie_handler/set-cookie.php')
    URL_CHECK_COOKIE = URL(
        'http://moth/w3af/core/cookie_handler/has-cookie.php')

    def test_low_level(self):
        opener = urllib2.build_opener(CookieHandler)
        # With this request the CookieHandler should store a cookie in its
        # cookiejar
        set_cookie_req = HTTPRequest(self.URL_SENDS_COOKIE)
        opener.open(set_cookie_req).read()

        # And now it will send it because we're setting cookie to True
        with_cookie_req = HTTPRequest(self.URL_CHECK_COOKIE, cookies=True)
        with_cookie_res = opener.open(with_cookie_req).read()
        self.assertTrue('Cookie was sent.' in with_cookie_res)

        # And now it will NOT send any cookie because we're setting cookie to False
        no_cookie_req = HTTPRequest(self.URL_CHECK_COOKIE, cookies=False)
        no_cookie_res = opener.open(no_cookie_req).read()
        self.assertTrue('Cookie was NOT sent.' in no_cookie_res)

        # And now it will send it because we're setting cookie to True
        with_cookie_req = HTTPRequest(self.URL_CHECK_COOKIE, cookies=True)
        with_cookie_res = opener.open(with_cookie_req).read()
        self.assertTrue('Cookie was sent.' in with_cookie_res)

    def test_xurllib(self):
        uri_opener = ExtendedUrllib()
        uri_opener.GET(self.URL_SENDS_COOKIE)

        resp = uri_opener.GET(self.URL_CHECK_COOKIE, cookies=True)
        self.assertTrue('Cookie was sent.' in resp)

        resp = uri_opener.GET(self.URL_CHECK_COOKIE, cookies=False)
        self.assertTrue('Cookie was NOT sent.' in resp)

        resp = uri_opener.GET(self.URL_CHECK_COOKIE, cookies=True)
        self.assertTrue('Cookie was sent.' in resp)
