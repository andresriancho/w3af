'''
test_blank_body.py

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
from plugins.grep.blank_body import blank_body


class test_blank_body(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = blank_body()
        self.url = url_object('http://www.w3af.com/')
        self.request = fuzzableRequest(self.url)
    
    def test_blank_body(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('blank_body', 'blank_body')) , 1 )
    
    def test_blank_body_none(self):
        body = 'header body footer'
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin.grep(self.request, response)
        self.assertEqual( len(kb.kb.getData('ssn', 'ssn')) , 0 )
    
    def test_blank_body_method(self): 
        body = ''
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        request = fuzzableRequest(self.url, method='ARGENTINA')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('ssn', 'ssn')) , 0 )
    
    def test_blank_body_code(self):
        body = ''
        headers = {'content-type': 'text/html'}
        response = httpResponse(401, body , headers, self.url, self.url)
        request = fuzzableRequest(self.url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('blank_body', 'blank_body')) , 0 )
