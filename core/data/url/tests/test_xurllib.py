# -*- coding: utf-8 -*-
'''
test_httpResponse.py

Copyright 2011 Andres Riancho

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
import time

import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb

from core.data.url.xUrllib import xUrllib
from core.data.parsers.urlParser import url_object
from core.controllers.misc.temp_dir import create_temp_dir, remove_temp_dir


class TestXUrllib(unittest.TestCase):
    
    def setUp(self):
        # The next cleanup() calls are here because some other test is leaving
        # the cf/kb objects in an inconsistent state and I need to clean them
        # before starting my own tests.
        cf.cf.cleanup()
        kb.kb.cleanup()
        
        cf.cf.save('sessionName',
                'defaultSession' + '-' + time.strftime('%Y-%b-%d_%H-%M-%S'))
        self.uri_opener = xUrllib()
        create_temp_dir()
        
    def tearDown(self):
        remove_temp_dir()
        kb.kb.cleanup()
        cf.cf.cleanup()
        
    def test_basic(self):
        url = url_object('http://www.google.com.ar/')
        body = self.uri_opener.GET( url ).getBody()
        self.assertTrue( 'Google' in body )
    
    def test_qs_params(self):
        url = url_object('http://www.google.com.ar/search?sourceid=chrome&ie=UTF-8&q=google')
        self.assertTrue( 'Google Maps' in self.uri_opener.GET( url ).getBody() )

        url = url_object('http://www.google.com.ar/search?sourceid=chrome&ie=UTF-8&q=yahoo')
        self.assertFalse( 'Google Maps' in self.uri_opener.GET( url ).getBody() )

    def test_gzip(self):
        url = url_object('http://www.google.com.ar/')
        res = self.uri_opener.GET( url )
        headers = res.getHeaders()
        content_encoding = headers.get('Content-Encoding', '')
        self.assertTrue('gzip' in content_encoding or 'compress' in content_encoding )
