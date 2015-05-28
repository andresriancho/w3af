"""
test_symfony.py

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
from functools import partial

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.symfony import symfony


class test_symfony(unittest.TestCase):

    SYMFONY_HEADERS = Headers([('content-type', 'text/html'),
                               ('set-cookie', 'symfony=sfasfasfa')])
    NON_SYMFONY_HEADERS = Headers([('content-type', 'text/html')])

    EMPTY_BODY = ''
    UNPROTECTED_BODY = """<html><head></head><body><form action="login" method="post">
                            <input type="text" name="signin" id="signin" /></form></body>
                          </html>"""
    PROTECTED_BODY = """<html><head></head><body><form action="login" method="post">
                            <input type="text" name="signin" id="signin" /><input type="hidden"
                            name="signin[_csrf_token]" value="069092edf6b67d5c25fd07642a54f6e3"
                            id="signin__csrf_token" /></form></body></html>"""

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = symfony()
        self.url = URL('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)
        self.http_resp = partial(
            HTTPResponse, code=200, geturl=self.url, original_url=self.url, _id=1)

    def tearDown(self):
        self.plugin.end()

    def test_symfony_positive(self):
        response = self.http_resp(
            read=self.EMPTY_BODY, headers=self.SYMFONY_HEADERS)
        self.assertTrue(self.plugin.symfony_detected(response))

    def test_symfony_negative(self):
        response = self.http_resp(
            read=self.EMPTY_BODY, headers=self.NON_SYMFONY_HEADERS)
        self.assertFalse(self.plugin.symfony_detected(response))

    def test_symfony_override(self):
        self.plugin._override = True
        response = self.http_resp(read=self.EMPTY_BODY,
                                  headers=self.SYMFONY_HEADERS)
        self.assertTrue(self.plugin.symfony_detected(response))

    def test_symfony_csrf_positive(self):
        response = self.http_resp(read=self.PROTECTED_BODY,
                                  headers=self.SYMFONY_HEADERS)
        self.assertTrue(self.plugin.has_csrf_token(response))

    def test_symfony_csrf_negative(self):
        response = self.http_resp(read=self.UNPROTECTED_BODY,
                                  headers=self.SYMFONY_HEADERS)
        self.assertFalse(self.plugin.has_csrf_token(response))

    def test_symfony_protected(self):
        response = self.http_resp(
            read=self.PROTECTED_BODY, headers=self.SYMFONY_HEADERS)
        request = FuzzableRequest(self.url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('symfony', 'symfony')), 0)

    def test_symfony_unprotected(self):
        request = FuzzableRequest(self.url, method='GET')
        response = self.http_resp(
            read=self.UNPROTECTED_BODY, headers=self.SYMFONY_HEADERS)
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('symfony', 'symfony')), 1)
