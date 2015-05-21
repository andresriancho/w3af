"""
test_rnd_param.py

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.url import parse_qs
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.plugins.evasion.rnd_param import rnd_param


class TestEvasion(unittest.TestCase):

    def setUp(self):
        self.eplugin = rnd_param()

    def test_add_when_empty(self):
        url = URL('http://www.w3af.com/')
        original_req = HTTPRequest(url)

        modified_req = self.eplugin.modify_request(original_req)
        self.assertEqual(len(modified_req.url_object.querystring), 1)

    def test_add_when_qs(self):
        url = URL('http://www.w3af.com/?id=1')
        original_req = HTTPRequest(url)

        modified_req = self.eplugin.modify_request(original_req)
        self.assertEqual(len(modified_req.url_object.querystring), 2)
        self.assertIn('id=1', str(modified_req.url_object.querystring))

    def test_add_when_qs_and_postdata(self):
        url = URL('http://www.w3af.com/?id=1')
        original_req = HTTPRequest(url, data='a=b')

        modified_req = self.eplugin.modify_request(original_req)
        self.assertEqual(len(modified_req.url_object.querystring), 2)
        self.assertIn('id=1', str(modified_req.url_object.querystring))
        
        data = parse_qs(modified_req.get_data())
        self.assertEqual(len(data), 2)
        self.assertIn('a=b', str(data))

        modified_qs = modified_req.url_object.querystring
        self.assertEqual(len(modified_qs), 2)
