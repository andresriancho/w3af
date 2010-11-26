import random
import unittest
import string

from guppy import hpy

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.temp_persist import disk_list


class test_disk_list(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_bloom_int(self):
        dl = disk_list()

        for i in xrange(0, 1000):
             _ = dl.append(i)

        for i in xrange(0, 1000 / 2 ):
            r = random.randint(0,1000-1)
            self.assertEqual(r in dl, True)

        for i in xrange(0, 1000 / 2 ):
            r = random.randint(1000,1000 * 2)
            self.assertEqual(r in dl, False)
        
    def test_bloom_string(self):
        dl = disk_list()

        for i in xrange(0, 1000):
            rnd = ''.join(random.choice(string.letters) for i in xrange(40))
            _ = dl.append(rnd)

        self.assertEqual(rnd in dl, True)

        for i in string.letters:
            self.assertEqual(i in dl, False)

        self.assertEqual(rnd in dl, True)

if __name__ == '__main__':
    unittest.main()

