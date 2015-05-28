"""
test_rnd_path.py

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
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.plugins.evasion.rnd_path import rnd_path


class TestEvasion(unittest.TestCase):
    
    def test_add_path_to_base_url(self):
        rp = rnd_path()

        u = URL('http://www.w3af.com/')
        r = HTTPRequest( u )
        url_string = rp.modify_request( r ).url_object.url_string
        
        self.assertRegexpMatches(url_string, 'http://www.w3af.com/\w*/../')
        
    def test_add_path_to_path_url(self):
        rp = rnd_path()
        
        u = URL('http://www.w3af.com/abc/')
        r = HTTPRequest( u )
        url_string = rp.modify_request( r ).url_object.url_string
        
        self.assertRegexpMatches(url_string, 'http://www.w3af.com/\w*/../abc/')
    
    def test_add_with_filename(self):
        rp = rnd_path()
        
        u = URL('http://www.w3af.com/abc/def.htm')
        r = HTTPRequest( u )
        url_string = rp.modify_request( r ).url_object.url_string
        
        self.assertRegexpMatches(url_string, 'http://www.w3af.com/\w*/../abc/def.htm')

    def test_add_with_qs(self):
        rp = rnd_path()
        
        u = URL('http://www.w3af.com/abc/def.htm?id=1')
        r = HTTPRequest( u )
        url_string = rp.modify_request( r ).url_object.url_string
        
        self.assertRegexpMatches(url_string, 'http://www.w3af.com/\w*/../abc/def.htm\?id=1')
        