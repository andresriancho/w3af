# -*- coding: UTF-8 -*-

import unittest

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.disk_set import disk_set

from core.data.parsers.urlParser import url_object
from core.data.request.httpQsRequest import HTTPQSRequest
from core.data.request.httpPostDataRequest import httpPostDataRequest


class test_disk_set(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_add(self):
        ds = disk_set()
        ds.add(1)
        ds.add(2)
        ds.add(3)
        ds.add(1)
        
        self.assertEqual( list(ds), [1,2,3])

    def test_add_urlobject(self):
        ds = disk_set()

        ds.add( url_object('http://w3af.org/?id=2') )
        ds.add( url_object('http://w3af.org/?id=3') )
        ds.add( url_object('http://w3af.org/?id=3') )
        
        self.assertEqual( ds[0] , url_object('http://w3af.org/?id=2'))
        self.assertEqual( ds[1] , url_object('http://w3af.org/?id=3'))
        self.assertEqual( len(ds) , 2)
        self.assertFalse( url_object('http://w3af.org/?id=4') in ds )
        self.assertTrue( url_object('http://w3af.org/?id=2') in ds )
        
    def test_add_HTTPQSRequest(self):
        ds = disk_set()
        
        uri = url_object('http://w3af.org/?id=2')
        qsr1 = HTTPQSRequest(uri, method='GET', headers={'Referer': 'http://w3af.org/'})

        uri = url_object('http://w3af.org/?id=3')
        qsr2 = HTTPQSRequest(uri, method='GET', headers={'Referer': 'http://w3af.com/'})
        
        uri = url_object('http://w3af.org/?id=7')
        qsr3 = HTTPQSRequest(uri, method='FOO', headers={'Referer': 'http://w3af.com/'})
        
        ds.add( qsr1 )
        ds.add( qsr2 )
        ds.add( qsr2 )
        ds.add( qsr1 )
        
        self.assertEqual( ds[0] , qsr1)
        self.assertEqual( ds[1] , qsr2)
        self.assertFalse( qsr3 in ds )
        self.assertTrue( qsr2 in ds )
        self.assertEqual( len(ds) , 2)
        
        # This forces an internal change in the URL object
        qsr2.getURL().url_string
        self.assertTrue( qsr2 in ds )

    def test_add_httpPostDataRequest(self):
        ds = disk_set()
        
        uri = url_object('http://w3af.org/?id=2')
        pdr1 = httpPostDataRequest(uri, method='GET', headers={'Referer': 'http://w3af.org/'})

        uri = url_object('http://w3af.org/?id=3')
        pdr2 = httpPostDataRequest(uri, method='GET', headers={'Referer': 'http://w3af.com/'})
        
        uri = url_object('http://w3af.org/?id=7')
        pdr3 = httpPostDataRequest(uri, method='FOO', headers={'Referer': 'http://w3af.com/'})
        
        ds.add( pdr1 )
        ds.add( pdr2 )
        ds.add( pdr2 )
        ds.add( pdr1 )
        
        self.assertEqual( ds[0] , pdr1)
        self.assertEqual( ds[1] , pdr2)
        self.assertFalse( pdr3 in ds )
        self.assertTrue( pdr2 in ds )
        self.assertEqual( len(ds) , 2)
        
        # This forces an internal change in the URL object
        pdr2.getURL().url_string
        self.assertTrue( pdr2 in ds )
                
    def test_update(self):
        ds = disk_set()
        ds.add(1)
        ds.update([2,3,1])
        
        self.assertEqual( list(ds), [1,2,3])
        
if __name__ == '__main__':
    unittest.main()

