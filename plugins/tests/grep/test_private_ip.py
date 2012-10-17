'''
test_private_ip.py

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

import core.data.kb.knowledgeBase as kb

from core.data.url.HTTPResponse import HTTPResponse
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.parsers.urlParser import url_object
from plugins.grep.private_ip import private_ip


class test_private_ip(unittest.TestCase):
    
    def setUp(self):
        kb.kb.cleanup()
        self.plugin = private_ip()
        self.url = url_object('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()
        
    def test_private_ip_empty(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'HTML')) , 0 )
    
    def test_private_ip_find(self):
        body = '<html><head>192.168.1.1</head></html>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'HTML')) , 1 )
    
    def test_private_ip_broken_html(self):
        body = '<html><head>192.168.1.1</html>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'HTML')) , 1 )
    
    def test_private_ip_find_10(self):
        body = 'header 10.2.34.2 footer'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'HTML')) , 1 )
    
    def test_private_ip_find_header(self):
        body = 'header content footer'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'x-via': '10.3.4.5'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'header')) , 1 )

    def test_private_ip_no(self):
        body = '<script> 1010.2.3.4 </script>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html', 'x-via': '10.256.3.10.1.2.3'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.get('private_ip', 'HTML')) , 0 )
        self.assertEquals( len(kb.kb.get('private_ip', 'header')) , 0 )
