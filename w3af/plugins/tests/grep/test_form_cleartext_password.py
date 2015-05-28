"""
test_form_cleartext_password.py

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

import w3af.core.data.kb.knowledge_base as kb
from w3af.plugins.grep.form_cleartext_password import form_cleartext_password
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class TestFormCleartextPassword(unittest.TestCase):

    def setUp(self):
        self.plugin = form_cleartext_password()
        kb.kb.clear('form_cleartext_password', 'form_cleartext_password')

    def tearDown(self):
        self.plugin.end()

    #Vulnerable to insecure form data submission over HTTP
    def test_vs1(self, *args):
        body = 'header <form action="http://www.w3af.com/">' \
               '<input type="password" name="passwd">' \
               '<input type="textarea"></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('form_cleartext_password',
                                       'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password', 'form_cleartext_password')
            [0].get_name() == 'Insecure password submission over HTTP', 1)

    def test_vs2(self, *args):
        body = 'header <form action="http://www.w3af.com/">' \
               '<input type="password" name="passwd" /></form>footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password','form_cleartext_password')
            [0].get_name() =='Insecure password submission over HTTP', 1)

    def test_vs3(self, *args):
        body = 'header <form><input type="password" name="passwd" />' \
               '</form>footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password','form_cleartext_password')
            [0].get_name() == 'Insecure password submission over HTTP', 1)

    def test_vs4(self, *args):
        body = 'header <form action="http://www.w3af.com/"><div>' \
               '<input type="password" name="passwd" /></div></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password','form_cleartext_password')
            [0].get_name() == 'Insecure password submission over HTTP', 1)

    def test_vs5(self, *args):
        body = 'header <form action="http://www.w3af.com/"><div></div>' \
               '</form><input type="password" name="passwd" />footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password','form_cleartext_password')
            [0].get_name() =='Insecure password submission over HTTP', 1)

    def test_m1(self, *args):
        """
        Vulnerable to MITM since login form was submitted over HTTP
        """
        body = 'header <form action="https://www.w3af.com/">' \
               '<input type="password" name="passwd" /></form>footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password','form_cleartext_password')
            [0].get_name() == 'Insecure password form access over HTTP', 1)

    def test_d1(self, *args):
        """
        Vulnerable to MITM with double password input
        """
        body = 'header <form action="https://www.w3af.com/">' \
               '<input type="password" name="passwd1" />' \
               '<input type="password" name="passwd2" />' \
               '</form>footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 1)
        self.assertEqual(
            kb.kb.get('form_cleartext_password', 'form_cleartext_password')
            [0].get_name() == 'Insecure password form access over HTTP', 1)

    def test_n1(self, *args):
        """
        Not vulnerable
        """
        body = 'header <form action="https://www.w3af.com/">' \
               '<input type="text" /></form>footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n2(self, *args):
        body = 'header <form action="https://www.w3af.com/"> ' \
               '<input type="password" name="passwd" /></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n3(self, *args):
        body = 'header <form action="https://www.notw3af.com/">' \
               '<input type="password" name="passwd"></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n4(self, *args):
        body = 'header <form action="/">' \
               '<input type="password" name="passwd"></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n5(self, *args):
        body = 'header <form>' \
               '<input type="password" name="passwd"></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n6(self, *args):
        body = 'header <form>' \
               '<input type="password" name="passwd"></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n7(self, *args):
        body = 'header <form><div>' \
               '<input type="password" name="passwd" /></div></form>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)

    def test_n8(self, *args):
        body = 'header <form><div></div></form>' \
               '<input type="password" name="passwd" />footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(
            len(kb.kb.get('form_cleartext_password',
                          'form_cleartext_password')), 0)