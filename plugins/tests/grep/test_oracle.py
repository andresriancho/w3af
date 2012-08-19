'''
test_oracle.py

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
from core.data.request.fuzzable_request import fuzzable_request
from core.data.parsers.urlParser import url_object
from core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
from core.controllers.misc.temp_dir import create_temp_dir
from plugins.grep.oracle import oracle


class test_oracle(unittest.TestCase):
    
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        fingerprint_404_singleton( [False, False, False] )
        self.plugin = oracle()

    def tearDown(self):
        self.plugin.end()
                
    def test_oracle_empty(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('oracle', 'oracle')) , 0 )
    
    def test_oracle_long(self):
        body = 'ABC ' * 10000
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('oracle', 'oracle')) , 0 )
    
    def test_oracle_positive(self):
        body = 'ABC ' * 100
        body += '<!-- Created by Oracle '
        body += '</br> ' * 50
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzable_request(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual( len(kb.kb.getData('oracle', 'oracle')) , 1 )
