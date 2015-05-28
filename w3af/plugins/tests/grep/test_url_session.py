"""
test_url_session.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import unittest

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.url_session import url_session


class TestURLInSession(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = url_session()

    def tearDown(self):
        self.plugin.end()

    def test_url_session_false(self):
        body = 'abc'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)
        
        self.plugin.grep(request, resp)
        
        infos = kb.kb.get('url_session', 'url_session')
        self.assertEquals(len(infos), 0)
    
    def test_url_session_in_url(self):
        body = 'abc'
        url = URL('http://www.w3af.com/?JSESSIONID=231badb19b93e44f47da1bd64a8147f2')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)
        
        self.plugin.grep(request, resp)
        
        infos = kb.kb.get('url_session', 'url_session')
        self.assertEquals(len(infos), 1)
        
        info = infos[0]
        self.assertEqual(info.get_name(), 'Session ID in URL')       
    
    def test_url_session_in_body(self):
        url = 'http://www.w3af.com/?JSESSIONID=231badb19b93e44f47da1bd64a8147f2'
        body = 'abc <a href="%s">def</a> footer' % url
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)
        
        self.plugin.grep(request, resp)
        
        infos = kb.kb.get('url_session', 'url_session')
        self.assertEquals(len(infos), 1)
        
        info = infos[0]
        self.assertEqual(info.get_name(), 'Session ID in URL')
    
    def test_url_session_in_body_and_url(self):
        url = 'http://www.w3af.com/?JSESSIONID=231badb19b93e44f47da1bd64a8147f2'
        body = 'abc <a href="%s">def</a> footer' % url
        url = URL(url)
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)
        
        self.plugin.grep(request, resp)
        
        infos = kb.kb.get('url_session', 'url_session')
        self.assertEquals(len(infos), 1)
        
        info = infos[0]
        self.assertEqual(info.get_name(), 'Session ID in URL')