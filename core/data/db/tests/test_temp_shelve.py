# -*- coding: UTF-8 -*-
'''
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

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.temp_shelve import temp_shelve


class test_shelve(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_int(self):
        tshelve = temp_shelve()
        for i in xrange(100):
            tshelve[ i ] = i
        self.assertEqual( len(tshelve) , 100 )
        self.assertEqual( tshelve[50] , 50 )

    def test_get(self):
        tshelve = temp_shelve()
        
        tshelve[0] = 'abc'
        abc1 = tshelve.get(0)
        abc2 = tshelve.get(0, 1)
        two = tshelve.get(1, 2)
        self.assertEqual( abc1 , 'abc' )
        self.assertEqual( abc2 , 'abc' )
        self.assertEqual( two , 2 )
    
    def test_keys(self):
        tshelve = temp_shelve()
        
        tshelve['a'] = 'abc'
        tshelve['b'] = 'abc'
        tshelve['c'] = 'abc'
        
        self.assertEqual( set(tshelve.keys()), set(['a','b','c']) )
    
    def test_iterkeys(self):
        tshelve = temp_shelve()
        
        tshelve['a'] = 'abc'
        tshelve['b'] = 'abc'
        tshelve['c'] = 'abc'
        
        self.assertEqual( set(tshelve.iterkeys()), set(['a','b','c']) )
