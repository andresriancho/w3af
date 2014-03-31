# -*- coding: utf-8 -*-
"""
test_data_container.py

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
import urllib

from w3af.core.data.dc.data_container import DataContainer
from nose.plugins.skip import SkipTest


class TestDataContainer(unittest.TestCase):
    
    def test_basic(self):
        dc = DataContainer([(u'a',['1']), (u'b', ['2','3'])])
        
        self.assertIn('a', dc)
        self.assertIn('b', dc)
        
        self.assertEqual(dc['a'], ['1'])
        self.assertEqual(dc['b'], ['2', '3'])
    
    def test_str(self):
        dc = DataContainer([(u'a',['1']), (u'b', ['2','3'])])
        str_dc = str(dc)
        self.assertEqual(str_dc, 'a=1&b=2&b=3')
        self.assertIsInstance(str_dc, str) 
        
        dc = DataContainer([(u'aaa', [''])])
        self.assertEqual(str(dc), 'aaa=')
        
        dc = DataContainer([(u'aaa', ('', ''))])
        self.assertEqual(str(dc), 'aaa=&aaa=')
    
    def test_str_special_chars(self):
        dc = DataContainer([(u'a',['1']), (u'u', [u'Ú-ú-Ü-ü'])], 'latin1')
        decoded_str = urllib.unquote(str(dc)).decode('latin-1')
        self.assertEquals(u'a=1&u=Ú-ú-Ü-ü', decoded_str)
        
    def test_unicode(self):
        dc = DataContainer([(u'a',['1']), (u'b', ['2','3'])])
        udc = unicode(dc)
        
        self.assertEqual(udc, u'a=1&b=2&b=3')
        self.assertIsInstance(udc, unicode)
        
        