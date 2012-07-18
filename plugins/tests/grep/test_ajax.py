'''
test_ajax.py

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

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.controllers.misc.temp_dir import create_temp_dir
from core.data.parsers.urlParser import url_object
from plugins.grep.ajax import ajax


class test_ajax(unittest.TestCase):
    
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = ajax()
        self.url = url_object('http://www.w3af.com/')
        self.request = fuzzableRequest(self.url)
        
    def test_ajax_empty(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 0 )
    
    def test_ajax_find(self):
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true); </script></head><html>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 1 )
    
    def test_ajax_broken_html(self):
        kb.kb.save('ajax','ajax',[])
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true); </head><html>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 1 )
    
    def test_ajax_broken_2(self):
        kb.kb.save('ajax','ajax',[])
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true);'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 1 )
    
    def test_ajax_find_2(self):
        kb.kb.save('ajax','ajax',[])
        body = '<html><head><script> ... xhr = new ActiveXObject("Microsoft.XMLHTTP"); ... </script></head><html>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        a = ajax()
        a.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 1 )
    
    def test_ajax_two(self):
        kb.kb.save('ajax','ajax',[])
        body = '<script> ... xhr = new XMLHttpRequest(); ... xhr = new ActiveXObject("Microsoft.XMLHTTP"); ... </script>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('ajax', 'ajax')) , 1 )
