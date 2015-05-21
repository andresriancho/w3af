"""
test_rnd_case.py

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
from w3af.plugins.evasion.rnd_case import rnd_case


class TestEvasion(unittest.TestCase):
    
    def test_no_modification(self):
        rc = rnd_case()
        
        u = URL('http://www.w3af.com/')
        r = HTTPRequest( u )
        self.assertEqual(rc.modify_request( r ).url_object.url_string,
                         u'http://www.w3af.com/')

    def test_modify_path(self):
        rc = rnd_case()
        
        u = URL('http://www.w3af.com/ab/')
        r = HTTPRequest( u )
        
        modified_path = rc.modify_request( r ).url_object.get_path()
        self.assertIn(modified_path, ['/ab/','/aB/','/Ab/','/AB/'])

    def test_modify_post_data(self):
        rc = rnd_case()
        
        u = URL('http://www.w3af.com/')
        r = HTTPRequest( u, data='a=b' )
        modified_data = rc.modify_request( r ).get_data()
        self.assertIn(modified_data, ['a=b','A=b','a=B','A=B'])

    def test_modify_path_file(self):
        rc = rnd_case()
        
        u = URL('http://www.w3af.com/a/B')
        r = HTTPRequest( u )
        options = ['/a/b','/a/B','/A/b','/A/B']
        modified_path = rc.modify_request( r ).url_object.get_path()
        self.assertIn(modified_path, options)

        #
        #    The plugins should not modify the original request
        #
        self.assertEqual(u.url_string, u'http://www.w3af.com/a/B')