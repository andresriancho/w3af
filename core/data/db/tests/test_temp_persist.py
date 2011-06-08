import random
from random import choice
import unittest
import string

from guppy import hpy

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.temp_persist import disk_list


class test_disk_list(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_int(self):
        dl = disk_list()

        for i in xrange(0, 1000):
             _ = dl.append(i)

        for i in xrange(0, 1000 / 2 ):
            r = random.randint(0,1000-1)
            self.assertEqual(r in dl, True)

        for i in xrange(0, 1000 / 2 ):
            r = random.randint(1000,1000 * 2)
            self.assertEqual(r in dl, False)
        
    def test_string(self):
        dl = disk_list()

        for i in xrange(0, 1000):
            rnd = ''.join(random.choice(string.letters) for i in xrange(40))
            _ = dl.append(rnd)

        self.assertEqual(rnd in dl, True)

        for i in string.letters:
            self.assertEqual(i in dl, False)

        self.assertEqual(rnd in dl, True)

    def test_len(self):
        dl = disk_list()

        for i in xrange(0, 100):
            _ = dl.append(i)

        self.assertEqual( len(dl) == 100, True)

    def test_pickle(self):
        dl = disk_list()

        dl.append( 'a' )
        dl.append( 1 )
        dl.append( [3,2,1] )

        values = []
        for i in dl:
            values.append(i)
        
        self.assertEqual( values[0] == 'a', True)
        self.assertEqual( values[1] == 1, True)
        self.assertEqual( values[2] == [3,2,1], True)

    def test_getitem(self):
        dl = disk_list()

        dl.append( 'a' )
        dl.append( 1 )
        dl.append( [3,2,1] )

        self.assertEqual( dl[0] == 'a', True)
        self.assertEqual( dl[1] == 1  , True)
        self.assertEqual( dl[2] == [3,2,1], True)

if __name__ == '__main__':
    unittest.main()

