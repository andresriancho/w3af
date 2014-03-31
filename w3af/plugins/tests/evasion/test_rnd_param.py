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

from w3af.core.data.parsers.url import URL
from w3af.core.data.parsers.url import parse_qs
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.plugins.evasion.rnd_param import rnd_param


class TestEvasion(unittest.TestCase):
    
    def test_add_when_empty(self):
        rp = rnd_param()

        u = URL('http://www.w3af.com/')
        r = HTTPRequest( u )
        qs = rp.modify_request( r ).url_object.querystring
        self.assertEqual(len(qs), 1)

    def test_add_when_qs(self):
        rp = rnd_param()
                
        u = URL('http://www.w3af.com/?id=1')
        r = HTTPRequest( u )
        qs = rp.modify_request( r ).url_object.querystring
        self.assertEqual(len(qs), 2)

    def test_add_when_qs_and_postdata(self):
        rp = rnd_param()
        
        u = URL('http://www.w3af.com/?id=1')
        r = HTTPRequest( u, data='a=b' )
        modified_request = rp.modify_request( r )

        data = parse_qs( modified_request.get_data() )
        self.assertEqual(len(data), 2)

        modified_qs = modified_request.url_object.querystring
        self.assertEqual(len(modified_qs), 2)
