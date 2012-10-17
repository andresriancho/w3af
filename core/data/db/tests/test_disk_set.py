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

from nose.plugins.attrib import attr

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.disk_set import disk_set

from core.data.parsers.urlParser import url_object
from core.data.request.HTTPQsRequest import HTTPQSRequest
from core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from core.data.dc.headers import Headers


@attr('smoke')
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
        hdr = Headers([('Referer', 'http://w3af.org/')])
        
        qsr1 = HTTPQSRequest(uri, method='GET', headers=hdr)

        uri = url_object('http://w3af.org/?id=3')
        qsr2 = HTTPQSRequest(uri, method='GET', headers=hdr)
        
        uri = url_object('http://w3af.org/?id=7')
        qsr3 = HTTPQSRequest(uri, method='FOO', headers=hdr)
        
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

    def test_add_HTTPPostDataRequest(self):
        ds = disk_set()
        
        uri = url_object('http://w3af.org/?id=2')
        hdr = Headers([('Referer', 'http://w3af.org/')])
        
        pdr1 = HTTPPostDataRequest(uri, method='GET', headers=hdr)

        uri = url_object('http://w3af.org/?id=3')
        pdr2 = HTTPPostDataRequest(uri, method='GET', headers=hdr)
        
        uri = url_object('http://w3af.org/?id=7')
        pdr3 = HTTPPostDataRequest(uri, method='FOO', headers=hdr)
        
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

