'''
test_path_disclosure.py

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

from core.data.parsers.urlParser import url_object
from core.data.request.fuzzable_request import FuzzableRequest as FuzzableRequest
from core.data.url.HTTPResponse import HTTPResponse as HTTPResponse
from core.data.dc.headers import Headers
from plugins.grep.path_disclosure import path_disclosure


class test_path_disclosure(unittest.TestCase):

    def setUp(self):
        self.plugin = path_disclosure()
        kb.kb.cleanup()
        self.url = url_object('http://www.w3af.com/')
        self.header = Headers([('content-type', 'text/html')])
        self.request = FuzzableRequest(self.url, method='GET')

    def tearDown(self):
        self.plugin.end()
            
    def test_path_disclosure(self):
        
        res = HTTPResponse(200, 'header body footer' , self.header, self.url, self.url)
        self.plugin.grep( self.request, res )
        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals( len(infos), 0)
    
    def test_path_disclosure_positive(self):
        res = HTTPResponse(200, 'header /etc/passwd footer' , self.header, self.url, self.url)
        self.plugin.grep( self.request, res )
        
        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals( len(infos), 1 )
        
        path = infos[0]['path']
        self.assertEqual( path, '/etc/passwd' )
        
