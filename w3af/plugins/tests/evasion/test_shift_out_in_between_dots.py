"""
test_shift_out_in_between_dots.py

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
from unittest.case import skip

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.plugins.evasion.shift_out_in_between_dots import shift_out_in_between_dots


@skip('URL normalization breaks evasion. @see: 4fa67fbb')
class TestEvasion(unittest.TestCase):
    
    def test_no_modification(self):
        sosibd = shift_out_in_between_dots()

        u = URL('http://www.w3af.com/')
        r = HTTPRequest( u )
        
        self.assertEqual(sosibd.modify_request( r ).url_object.url_string,
                         u'http://www.w3af.com/')

    def test_add_when_dotdot(self):
        sosibd = shift_out_in_between_dots()
        
        u = URL('http://www.w3af.com/../')
        r = HTTPRequest( u )
        
        self.assertEqual(sosibd.modify_request( r ).url_object.url_string,
                         u'http://www.w3af.com/.%0E%0F./')

    def test_add_path_filename(self):
        sosibd = shift_out_in_between_dots()
        
        u = URL('http://www.w3af.com/abc/def/.././jkl.htm')
        r = HTTPRequest( u )
        
        self.assertEqual(sosibd.modify_request( r ).url_object.url_string,
                         u'http://www.w3af.com/abc/def/.%0E%0F././jkl.htm')
        #
        #    The plugins should not modify the original request
        #
        self.assertEqual(u.url_string, u'http://www.w3af.com/abc/def/.././jkl.htm')