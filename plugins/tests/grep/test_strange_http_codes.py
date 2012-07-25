'''
test_strange_http_codes.py

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
from core.data.parsers.urlParser import url_object
from core.controllers.misc.temp_dir import create_temp_dir
from core.controllers.coreHelpers.fingerprint_404 import fingerprint_404_singleton
from plugins.grep.strange_http_codes import strange_http_codes


class test_strange_http_codes(unittest.TestCase):
    
    def setUp(self):
        create_temp_dir()
        self.plugin = strange_http_codes()
        fingerprint_404_singleton( [False, False, False] )
            
    def test_strange_http_codes(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        request = fuzzableRequest(url, method='GET')
        
        resp_200 = httpResponse(200, body , headers, url, url)
        resp_404 = httpResponse(404, body , headers, url, url)
        KNOWN_GOOD = [resp_200, resp_404]
        
        resp_999 = httpResponse(999, body , headers, url, url)
        resp_123 = httpResponse(123, body , headers, url, url)
        resp_567 = httpResponse(567, body , headers, url, url)
        resp_666 = httpResponse(666, body , headers, url, url)
        resp_777 = httpResponse(777, body , headers, url, url)
        KNOWN_BAD = [resp_999, resp_123, resp_567, resp_666, resp_777]
        
        for resp in KNOWN_GOOD:
            kb.kb.cleanup()
            self.plugin.grep(request, resp)
            self.assertEquals( len(kb.kb.getData('strange_http_codes', 
                                                 'strange_http_codes')), 0)
        
        for resp in KNOWN_BAD:
            kb.kb.cleanup()
            self.plugin.grep(request, resp)
            self.assertEquals( len(kb.kb.getData('strange_http_codes', 
                                                 'strange_http_codes')), 1)
