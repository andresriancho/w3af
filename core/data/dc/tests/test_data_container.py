# -*- coding: utf-8 -*-
'''
test_data_container.py

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
import urllib

from core.data.dc.data_container import DataContainer
from nose.plugins.skip import SkipTest


class TestDataContainer(unittest.TestCase):
    
    def test_basic(self):
        dc = DataContainer([(u'a',['1']), (u'b', ['2','3'])])
        
        self.assertIn('a', dc)
        self.assertIn('b', dc)
        
        self.assertEqual(dc['a'], ['1'])
        self.assertEqual(dc['b'], ['2', '3'])
    
    def test_init_error_case01(self):
        msg = '''There is a problem with data containers: there is no
        type check for values passed to the init function, which ends
        with the following:
        
            DataContainer( [(u'a','123')] )
            dc['a'] == '123'
            
            DataContainer( [(u'a', ['123'])] )
            dc['a'] == ['123',]
        
        Which will cause bugs when someone does the following:
            dc['a'][0]
        
        Expecting to get '123' and gets '1'. This bug won't raise an exception
        (which makes it even harder to spot) but will in some cases prevent us
        from finding a vulnerability or following the right link.
        '''
        raise SkipTest(msg)
    
        self.assertRaises(TypeError, DataContainer, [(u'a','1')])

    def test_init_error_case02(self):
        self.assertRaises(TypeError, DataContainer, [(u'a','1'),
                                                     (u'a','1')])
        
    def test_str(self):
        dc = DataContainer([(u'a',['1']), (u'b', ['2','3'])])
        self.assertEqual(str(dc), 'a=1&b=2&b=3')        
        
        dc = DataContainer([(u'aaa', [''])])
        self.assertEqual(str(dc), 'aaa=')
        
        dc = DataContainer([(u'aaa', ('', ''))])
        self.assertEqual(str(dc), 'aaa=&aaa=')
         
        dc = DataContainer([(u'a',['1']), (u'u', [u'Ú-ú-Ü-ü'])], 'latin1')
        decoded_str = urllib.unquote(str(dc)).decode('latin-1')
        self.assertEquals(u'a=1&u=Ú-ú-Ü-ü', decoded_str)
        
        