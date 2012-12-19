'''
test_info.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import unittest

from nose.plugins.attrib import attr

from core.data.kb.info import Info
from core.data.parsers.url import URL

class MockInfo(Info):
    def __init__(self):
        desc = 'desc ' * 10
        super(MockInfo, self).__init__('TestCase', desc, 1, 'plugin_name')

@attr('smoke')
class TestInfo(unittest.TestCase):
    '''
    Simplest tests for info. Mainly started because of incompatibilities between
    nosetests, doctest and "_".

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def test_convert_to_range(self):
        inf = MockInfo()

        res = inf._convert_to_range_wrapper([1, 2, 3, 4, 5, 6])
        self.assertEquals('1 to 6', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6])
        self.assertEquals('1 to 3 and 6', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6, 7, 8])
        self.assertEquals('1 to 3, 6 to 8', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6, 7, 8, 10])
        self.assertEquals('1 to 3, 6 to 8 and 10', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 10, 20, 30])
        self.assertEquals('1 to 3, 10, 20 and 30', res)

        res = inf._convert_to_range_wrapper([1, 3, 10, 20, 30])
        self.assertEquals('1, 3, 10, 20 and 30', res)

        res = len(inf._convert_to_range_wrapper(range(0, 30000, 2)).split())
        self.assertEquals(15001, res)

    def test_set_uri(self):
        i = MockInfo()
        self.assertRaises(TypeError, i.set_uri, 'http://www.w3af.com/')
        
        uri = URL('http://www.w3af.com/')
        i.set_uri(uri)
        self.assertEqual(i.get_uri(), uri)

    def test_set_url(self):
        i = MockInfo()
        self.assertRaises(TypeError, i.set_url, 'http://www.w3af.com/?id=1')
        
        uri = URL('http://www.w3af.com/?id=1')
        url = URL('http://www.w3af.com/')
        
        i.set_url(uri)
        
        self.assertEqual(i.get_uri(), uri)
        self.assertEqual(i.get_url(), url)
    
    def test_set_desc(self):
        i = MockInfo()
        
        self.assertRaises(ValueError, i.set_desc, 'abc')
        
        desc = 'abc ' * 30
        i.set_desc(desc)
        self.assertTrue(i.get_desc().startswith(desc))