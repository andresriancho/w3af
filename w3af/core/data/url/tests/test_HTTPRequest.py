# -*- coding: utf-8 -*-
"""
test_HTTPRequest.py

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

import msgpack
from nose.plugins.attrib import attr

from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.request.fuzzable_request import FuzzableRequest


@attr('smoke')
class TestHTTPRequest(unittest.TestCase):

    def test_basic(self):
        u = URL('http://www.w3af.com')
        req = HTTPRequest(u)
        
        self.assertEqual(req.get_full_url(), 'http://www.w3af.com/')
        self.assertEqual(req.get_uri().url_string, 'http://www.w3af.com/')

    def test_to_from_dict(self):
        headers = Headers([('Host', 'www.w3af.com')])
        req = HTTPRequest(URL("http://www.w3af.com/"), data='spameggs',
                          headers=headers)

        msg = msgpack.dumps(req.to_dict())
        loaded_dict = msgpack.loads(msg)
        loaded_req = HTTPRequest.from_dict(loaded_dict)

        self.assertEqual(req, loaded_req)
        self.assertEqual(req.__dict__.values(),
                         loaded_req.__dict__.values())

    def test_to_dict_msgpack_with_data_token(self):
        token = DataToken('Host', 'www.w3af.com', ('Host',))
        headers = Headers([('Host', token)])
        freq = FuzzableRequest(URL("http://www.w3af.com/"), headers=headers)

        req = HTTPRequest.from_fuzzable_request(freq)

        msgpack.dumps(req.to_dict())
            
    def test_dump_case01(self):
        expected = '\r\n'.join(['GET http://w3af.com/a/b/c.php HTTP/1.1',
                                'Hello: World',
                                '',
                                ''])
        u = URL('http://w3af.com/a/b/c.php')
        headers = Headers([('Hello', 'World')])
        req = HTTPRequest(u, headers=headers)
        
        self.assertEqual(req.dump(), expected)

    def test_dump_case02(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: Múndo',
                                 u'',
                                 u''])
        u = URL('http://w3af.com/a/b/c.php')
        headers = Headers([('Hola', 'Múndo')])
        req = HTTPRequest(u, headers=headers)
        
        self.assertEqual(req.dump(), expected.encode('utf-8'))
