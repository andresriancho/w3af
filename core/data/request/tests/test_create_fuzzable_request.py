'''
test_create_fuzzable_request.py

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

from core.data.request.factory import create_fuzzable_request
from core.data.url.HTTPRequest import HTTPRequest
from core.data.parsers.urlParser import url_object

from core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from core.data.request.HTTPQsRequest import HTTPQSRequest
from core.data.request.JSONRequest import JSONPostDataRequest
from core.data.request.WebServiceRequest import WebServiceRequest
from core.data.request.XMLRPCRequest import XMLRPCRequest
from core.data.url.handlers.MultipartPostHandler import MultipartPostHandler


@attr('smoke')
class TestCreateFuzzableRequest(unittest.TestCase):

    def setUp(self):
        self.url = url_object('http://www.w3af.com/')
    
    def test_simplest(self):
        fr = create_fuzzable_request(self.url)
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), {} )
        self.assertEqual( fr.get_method(), 'GET' )
        
    def test_headers(self):
        fr = create_fuzzable_request(self.url, add_headers={'foo': 'bar'})
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), {'foo': 'bar'} )
        self.assertEqual( fr.get_method(), 'GET' )
        
    def test_headers_method(self):
        fr = create_fuzzable_request(self.url, method='PUT', 
                                     add_headers={'foo': 'bar'})
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), {'foo': 'bar'} )
        self.assertEqual( fr.get_method(), 'PUT' )

    def test_from_HTTPRequest(self):
        request = HTTPRequest(self.url)
        fr = create_fuzzable_request(request)
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.get_method(), 'GET' )

    def test_from_HTTPRequest_headers(self):
        request = HTTPRequest(self.url, headers={'Foo': 'bar'})
        fr = create_fuzzable_request(request)
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), {'Foo': 'bar'} )
        self.assertEqual( fr.get_method(), 'GET' )
        self.assertIsInstance( fr, HTTPQSRequest)
        
    def test_simple_post(self):
        post_data = 'a=b&d=3'
        headers = {'content-length': str(len(post_data))}
        
        fr = create_fuzzable_request(self.url, add_headers=headers, 
                                     post_data=post_data, method='POST')
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), headers )
        self.assertEqual( fr.get_method(), 'POST' )
        self.assertIsInstance( fr, HTTPPostDataRequest)

    def test_json_post(self):
        post_data = '{"1":"2"}'
        headers = {'content-length': str(len(post_data))}
        
        fr = create_fuzzable_request(self.url, add_headers=headers, 
                                     post_data=post_data, method='POST')
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), headers )
        self.assertEqual( fr.get_method(), 'POST' )
        self.assertIsInstance( fr, JSONPostDataRequest)

    def test_xmlrpc_post(self):
        post_data = '''<methodCall>
            <methodName>system.listMethods</methodName>
            <params></params>
        </methodCall>'''
        
        headers = {'content-length': str(len(post_data))}
        
        fr = create_fuzzable_request(self.url, add_headers=headers, 
                                     post_data=post_data, method='POST')
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), headers )
        self.assertEqual( fr.get_method(), 'POST' )
        self.assertIsInstance( fr, XMLRPCRequest)

    def test_multipart_post(self):
        '''
        This shows that:
            # Case #3 - multipart form data - prepare data container
        
        In factory.py doesn't really work. 
        '''
        boundary, post_data = MultipartPostHandler.multipart_encode( [('a', 'bcd'), ], []  )

        headers = {'content-length': str(len(post_data)) ,
                   'content-type': 'multipart/form-data'}
        
        fr = create_fuzzable_request(self.url, add_headers=headers, 
                                     post_data=post_data, method='POST')
        
        self.assertEqual( fr.getURL(), self.url )
        self.assertEqual( fr.getHeaders(), headers )
        self.assertEqual( fr.get_method(), 'POST' )
        self.assertEqual( fr.getData(), post_data)
        self.assertIsInstance( fr, HTTPPostDataRequest)
        