'''
test_symfony.py

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

from functools import partial

import core.data.kb.knowledgeBase as kb

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.controllers.misc.temp_dir import create_temp_dir
from core.data.parsers.urlParser import url_object
from plugins.grep.symfony import symfony


class test_symfony(unittest.TestCase):
    
    SYMFONY_HEADERS = {'set-cookie': 'symfony=sfasfasfa', 'content-type': 'text/html'}
    NON_SYMFONY_HEADERS = {'content-type': 'text/html'}
    
    EMPTY_BODY = ''
    UNPROTECTED_BODY = '''<html><head></head><body><form action="login" method="post">
                            <input type="text" name="signin" id="signin" /></form></body>
                          </html>'''
    PROTECTED_BODY = '''<html><head></head><body><form action="login" method="post">
                            <input type="text" name="signin" id="signin" /><input type="hidden"
                            name="signin[_csrf_token]" value="069092edf6b67d5c25fd07642a54f6e3"
                            id="signin__csrf_token" /></form></body></html>'''
    
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = symfony()
        self.url = url_object('http://www.w3af.com/')
        self.request = fuzzableRequest(self.url)
        self.http_resp = partial(httpResponse, code=200, geturl=self.url, original_url=self.url) 
    
    def test_symfony_positive(self):
        response = self.http_resp(read=self.EMPTY_BODY, info=self.SYMFONY_HEADERS)
        self.assertTrue( self.plugin.symfonyDetected(response) )
    
    def test_symfony_negative(self):
        response = self.http_resp(read=self.EMPTY_BODY, info=self.NON_SYMFONY_HEADERS)
        self.assertFalse( self.plugin.symfonyDetected(response) )
    
    def test_symfony_override(self):
        self.plugin._override = True
        response = self.http_resp(read=self.EMPTY_BODY, info=self.SYMFONY_HEADERS)
        self.assertTrue( self.plugin.symfonyDetected(response) )
    
    def test_symfony_csrf_positive(self):
        response = self.http_resp(read=self.PROTECTED_BODY, info=self.SYMFONY_HEADERS)
        self.assertTrue( self.plugin.csrfDetected(response.getDOM()) )
    
    def test_symfony_csrf_negative(self):
        response = self.http_resp(read=self.UNPROTECTED_BODY, info=self.SYMFONY_HEADERS)
        self.assertFalse( self.plugin.csrfDetected(response.getDOM()) )

    def test_symfony_protected(self):
        response = self.http_resp(read=self.PROTECTED_BODY, info=self.SYMFONY_HEADERS)
        request = fuzzableRequest(self.url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('symfony', 'symfony')) , 0 )
    
    def test_symfony_unprotected(self):
        request = fuzzableRequest(self.url, method='GET')
        response = self.http_resp(read=self.UNPROTECTED_BODY, info=self.SYMFONY_HEADERS)
        self.plugin.grep(request, response)
        self.assertEquals( len(kb.kb.getData('symfony', 'symfony')) , 1 )
