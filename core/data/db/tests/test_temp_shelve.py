# -*- coding: UTF-8 -*-

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
    
if __name__ == '__main__':
    unittest.main()
