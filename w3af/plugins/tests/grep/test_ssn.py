"""
test_ssn.py

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
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.plugins.grep.ssn import ssn


class test_ssn(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        self.plugin = ssn()
        self.plugin._already_inspected = set()
        self.url = URL('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_ssn_empty_string(self):
        body = ''
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin._already_inspected = set()
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('ssn', 'ssn')), 0)

    def test_ssn_separated(self):
        body = 'header 771-12-9876 footer'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 1)

    def test_ssn_with_html(self):
        body = 'header <b>771</b>-<b>12</b>-<b>9878</b> footer'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 1)

    def test_ssn_with_complex_html(self):
        """
        Test for false positive "...discloses a US Social Security Number: "12-56-1011"..."
        """
        body = """<select name="servers">
                    <option value="0" selected="selected">0</option>
                    <option value="1">1</option>
                    <option value="2-5">2-5</option>
                    <option value="6-10">6-10</option>
                    <option value="11-19">11-19</option>
                    <option value="20+">20+</option>
                </select>"""
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 0)

    def test_ssn_together(self):
        body = 'header 771129876 footer'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('ssn', 'ssn')), 1)

    def test_ssn_extra_number(self):
        body = 'header 7711298761 footer'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEqual(len(kb.kb.get('ssn', 'ssn')), 0)

    def test_find_ssn(self):
        EXPECTED = set([(None, None),
                      ('771129876', '771-12-9876'),
            ('771129876', '771-12-9876'),
            ('771 12 9876', '771-12-9876'),
            ('771 12 9876', '771-12-9876'),
            ('771 12 9876', '771-12-9876'),
            ('771129876', '771-12-9876')])

        res = []
        res.append(self.plugin._find_SSN(''))
        res.append(self.plugin._find_SSN('header 771129876 footer'))
        res.append(self.plugin._find_SSN('771129876'))
        res.append(self.plugin._find_SSN('header 771 12 9876 footer'))
        res.append(self.plugin._find_SSN('header 771 12 9876 32 footer'))
        res.append(self.plugin._find_SSN('header 771 12 9876 32 64 footer'))
        res.append(
            self.plugin._find_SSN('header 771129876 771129875 footer'))

        self.assertEqual(EXPECTED,
                         set(res))
