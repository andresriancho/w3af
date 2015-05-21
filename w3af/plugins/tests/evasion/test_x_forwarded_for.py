"""
test_x_forwarded_for.py

Copyright 2013 Andres Riancho

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
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.dc.headers import Headers
from w3af.plugins.evasion.x_forwarded_for import x_forwarded_for


class TestXForwardedFor(unittest.TestCase):
    
    def test_no_modification(self):
        xff = x_forwarded_for()

        u = URL('http://www.w3af.com/')
        headers = Headers([('X-Forwarded-For', '127.0.0.1')])
        r = HTTPRequest(u, headers=headers)
        
        modified_request = xff.modify_request( r )
        modified_headers = modified_request.get_headers()
        
        self.assertIn('X-forwarded-for', modified_headers)
        self.assertEqual(modified_headers['X-forwarded-for'],
                         u'127.0.0.1', modified_headers)

    def test_add_header(self):
        xff = x_forwarded_for()

        u = URL('http://www.w3af.com/')
        r = HTTPRequest(u)
        
        modified_request = xff.modify_request(r)
        modified_headers = modified_request.get_headers()
        
        self.assertIn('X-forwarded-for', modified_headers)
        self.assertEqual(modified_headers['X-forwarded-for'],
                         u'163.7.70.57', modified_headers)
