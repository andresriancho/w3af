# -*- coding: utf-8 -*-
'''
test_xurllib.py

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
import threading
import time
import Queue

from nose.plugins.attrib import attr

from core.data.url.xUrllib import xUrllib
from core.data.parsers.url import URL
from core.data.dc.data_container import DataContainer

from core.controllers.w3afException import (w3afMustStopByUserRequest,
                                            w3afMustStopOnUrlError)


@attr('smoke')
class TestXUrllib(unittest.TestCase):
    
    MOTH_MESSAGE = 'Welcome to the moth homepage!'
    
    def setUp(self):
        self.uri_opener = xUrllib()
        
    def test_basic(self):
        url = URL('http://moth/')
        http_response = self.uri_opener.GET( url, cache=False )
        self.assertTrue( self.MOTH_MESSAGE in http_response.body )
    
    def test_cache(self):
        url = URL('http://moth/')
        http_response = self.uri_opener.GET( url )
        self.assertTrue( self.MOTH_MESSAGE in http_response.body )
        
        url = URL('http://moth/')
        http_response = self.uri_opener.GET( url )
        self.assertTrue( self.MOTH_MESSAGE in http_response.body )
    
    def test_qs_params(self):
        url = URL('http://moth/w3af/audit/local_file_read/local_file_read.php?file=section.txt')
        http_response = self.uri_opener.GET( url, cache=False )
        self.assertTrue( 'Showing the section content.' in http_response.body, http_response.body )

        url = URL('http://moth/w3af/audit/local_file_read/local_file_read.php?file=/etc/passwd')
        http_response = self.uri_opener.GET( url, cache=False )
        self.assertTrue( 'root:x:0:0:' in http_response.body, http_response.body )

    def test_POST(self):
        url = URL('http://moth/w3af/audit/xss/dataReceptor2.php')
        data = DataContainer([('empresa', 'abc'), ('firstname', 'def')])
        http_response = self.uri_opener.POST( url, data, cache=False )
        self.assertTrue( 'def' in http_response.body, http_response.body )

    def test_POST_special_chars(self):
        url = URL('http://moth/w3af/audit/xss/dataReceptor2.php')
        test_data = 'abc<def>"-á-'
        data = DataContainer([('empresa', test_data), ('firstname', 'def')])
        http_response = self.uri_opener.POST( url, data, cache=False )
        self.assertTrue( test_data in http_response.body, http_response.body )

    def test_gzip(self):
        url = URL('http://www.google.com.ar/')
        res = self.uri_opener.GET( url, cache=False )
        headers = res.getHeaders()
        content_encoding, _ = headers.iget('content-encoding', '')
        test_res = 'gzip' in content_encoding or \
                   'compress' in content_encoding
        self.assertTrue(test_res, content_encoding)
    
    def test_get_cookies(self):
        self.assertEqual( len([c for c in self.uri_opener.get_cookies()]), 0 )
        
        url_sends_cookie = URL('http://moth/w3af/core/cookie_handler/set-cookie.php')
        self.uri_opener.GET( url_sends_cookie, cache=False )
        
        self.assertEqual( len([c for c in self.uri_opener.get_cookies()]), 1 )
        cookie = [c for c in self.uri_opener.get_cookies()][0]
        self.assertEqual( 'moth.local', cookie.domain )

    def test_unknown_url(self):
        url = URL('http://longsitethatdoesnotexistfoo.com/')
        self.assertRaises(w3afMustStopOnUrlError, self.uri_opener.GET, url)

    def test_stop(self):
        self.uri_opener.stop()
        url = URL('http://moth/')
        self.assertRaises(w3afMustStopByUserRequest, self.uri_opener.GET, url)
        
    def test_pause_stop(self):
        self.uri_opener.pause(True)
        self.uri_opener.stop()
        url = URL('http://moth/')
        self.assertRaises(w3afMustStopByUserRequest, self.uri_opener.GET, url)
        
    def test_pause(self):
        output = Queue.Queue()
        self.uri_opener.pause(True)
        
        def send(uri_opener, output):
            url = URL('http://moth/')
            http_response = uri_opener.GET(url)
            output.put(http_response)

        th = threading.Thread(target=send, args=(self.uri_opener, output))
        th.daemon = True
        th.start()
        
        self.assertRaises(Queue.Empty, output.get, True, 2)

    def test_pause_unpause(self):
        output = Queue.Queue()
        self.uri_opener.pause(True)
        
        def send(uri_opener, output):
            url = URL('http://moth/')
            http_response = uri_opener.GET(url)
            output.put(http_response)

        th = threading.Thread(target=send, args=(self.uri_opener, output))
        th.daemon = True
        th.start()
        
        self.assertRaises(Queue.Empty, output.get, True, 2)
        
        self.uri_opener.pause(False)
        
        http_response = output.get()

        self.assertEqual(http_response.getCode(), 200)
        self.assertTrue(self.MOTH_MESSAGE in http_response.body, http_response.body)
        
