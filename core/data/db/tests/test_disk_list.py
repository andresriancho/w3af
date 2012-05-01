# -*- coding: UTF-8 -*-

import random
import unittest
import string

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.disk_list import disk_list
from core.data.parsers.urlParser import url_object
from core.data.request.httpQsRequest import HTTPQSRequest


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
    
    def test_unicode(self):
        dl = disk_list()

        dl.append( u'à' )
        dl.append( u'המלצת השבוע' )
        dl.append( [u'à',] )
        
        self.assertEqual( dl[0] , u'à')
        self.assertEqual( dl[1] , u'המלצת השבוע')
        self.assertEqual( dl[2] , [u'à',])

    def test_urlobject(self):
        dl = disk_list()

        dl.append( url_object('http://w3af.org/?id=2') )
        dl.append( url_object('http://w3af.org/?id=3') )
        
        self.assertEqual( dl[0] , url_object('http://w3af.org/?id=2'))
        self.assertEqual( dl[1] , url_object('http://w3af.org/?id=3'))
        self.assertFalse( url_object('http://w3af.org/?id=4') in dl )
        self.assertTrue( url_object('http://w3af.org/?id=2') in dl )
        
    def test_fuzzable_request(self):
        dl = disk_list()
        
        uri = url_object('http://w3af.org/?id=2')
        qsr1 = HTTPQSRequest(uri, method='GET', headers={'Referer': 'http://w3af.org/'})

        uri = url_object('http://w3af.org/?id=3')
        qsr2 = HTTPQSRequest(uri, method='OPTIONS', headers={'Referer': 'http://w3af.com/'})
        
        uri = url_object('http://w3af.org/?id=7')
        qsr3 = HTTPQSRequest(uri, method='FOO', headers={'Referer': 'http://w3af.com/'})

        dl.append( qsr1 )
        dl.append( qsr2 )
        
        self.assertEqual( dl[0] , qsr1)
        self.assertEqual( dl[1] , qsr2)
        self.assertFalse( qsr3 in dl )
        self.assertTrue( qsr2 in dl )
        
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

    def test_not(self):
        dl = disk_list()
        self.assertFalse( dl )
    
    def test_extend(self):
        dl = disk_list()

        dl.append( 'a' )
        dl.extend( [1,2,3] )

        self.assertEqual( len(dl), 4)
        self.assertEqual( dl[0] , 'a')
        self.assertEqual( dl[1] , 1)
        self.assertEqual( dl[2] , 2)
        self.assertEqual( dl[3] , 3)
    
    def test_clear(self):
        dl = disk_list()

        dl.append( 'a' )
        dl.append( 'b' )
        
        self.assertEqual( len(dl), 2)
        
        dl.clear()
        
        self.assertEqual( len(dl), 0)
                
    def test_sorted(self):
        dl = disk_list()

        dl.append( 'abc' )
        dl.append( 'def' )
        dl.append( 'aaa' )
        
        sorted_dl = sorted(dl)
        
        self.assertEqual( ['aaa','abc','def'], sorted_dl)
    
    def test_ordered_iter(self):
        dl = disk_list()

        dl.append( 'abc' )
        dl.append( 'def' )
        dl.append( 'aaa' )
        
        sorted_dl = []
        for i in dl.ordered_iter():
            sorted_dl.append(i)
        
        self.assertEqual( ['aaa','abc','def'], sorted_dl)        
        
    def test_reverse_iteration(self):
        dl = disk_list()
        dl.append(1)
        dl.append(2)
        dl.append(3)
        
        reverse_iter_res = []
        for i in reversed(dl):
            reverse_iter_res.append(i)
        
        self.assertEqual( reverse_iter_res, [3,2,1])

if __name__ == '__main__':
    unittest.main()

