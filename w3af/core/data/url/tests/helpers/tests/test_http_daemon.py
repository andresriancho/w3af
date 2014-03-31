"""
test_http_daemon.py

Copyright 2013 Andres Riancho

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
import urllib2

from w3af.core.data.url.tests.helpers.http_daemon import HTTPDaemon


class TestHTTPDaemon(unittest.TestCase):
    """
    This is a unittest for the ServerHandler which lives in http_daemon.py
    
    @author: Andres Riancho <andres . riancho | gmail . com>
    """
    def setUp(self):
        self.http_daemon = HTTPDaemon()
        self.http_daemon.start()
        self.http_daemon.wait_for_start()
        
        self.requests = self.http_daemon.requests 
    
    def tearDown(self):
        self.http_daemon.shutdown()
    
    def test_simple_GET(self):
        url = 'http://%s:%s/hello' % ('127.0.0.1', self.http_daemon.get_port())
        response_body = urllib2.urlopen(url).read()
        
        self.assertEqual(response_body, 'ABCDEF\n')
        self.assertEqual(len(self.requests), 1)
        
        request = self.requests[0]
        
        self.assertEqual(request.path, '/hello')
        self.assertEqual(request.command, 'GET')
        self.assertEqual(request.request_version, 'HTTP/1.1')
        self.assertIn('host', request.headers)
        self.assertEqual(request.request_body, None)
        