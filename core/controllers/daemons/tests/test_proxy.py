'''
test_proxy.py

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
import urllib2
import unittest

from core.data.url.xUrllib import xUrllib
from core.controllers.misc.temp_dir import create_temp_dir
from core.controllers.daemons.proxy import proxy, w3afProxyHandler


class TestProxy(unittest.TestCase):
    
    IP = '127.0.0.1'
    PORT = 44445
    
    def setUp(self):
        # Start the proxy server
        create_temp_dir()
        self._proxy = proxy(self.IP, self.PORT, xUrllib(), w3afProxyHandler)
        self._proxy.start()
        
        # Build the proxy opener
        proxy_handler = urllib2.ProxyHandler({"http": "http://%s:%s" % (self.IP, self.PORT)})
        self.proxy_opener = urllib2.build_opener(proxy_handler,
                                                 urllib2.HTTPHandler)
    
    def test_do_req_through_proxy(self):
        resp_body = self.proxy_opener.open('http://moth').read()
        
        # Basic check
        self.assertTrue(len(resp_body) > 0)
        
        # Get response using the proxy
        proxy_resp = self.proxy_opener.open('http://moth')
        # Get it without any proxy
        direct_resp = urllib2.urlopen('http://moth')
        
        # Must be equal
        self.assertEqual(direct_resp.read(), proxy_resp.read())
        self.assertEqual(dict(direct_resp.info()), dict(proxy_resp.info()))

    def test_do_SSL_req_through_proxy(self):
        resp_body = self.proxy_opener.open('https://moth').read()
        
        # Basic check
        self.assertTrue(len(resp_body) > 0)
        
        # Get response using the proxy
        proxy_resp = self.proxy_opener.open('https://moth')
        # Get it without any proxy
        direct_resp = urllib2.urlopen('https://moth')
        
        # Must be equal
        self.assertEqual(direct_resp.read(), proxy_resp.read())
        self.assertEqual(dict(direct_resp.info()), dict(proxy_resp.info()))
    
    def test_prox_req_ok(self):
        '''Test if self._proxy.stop() works as expected. Note that the check 
        content is the same as the previous check, but it might be that this
        check fails because of some error in start() or stop() which is run
        during setUp and tearDown.'''
        # Get response using the proxy
        proxy_resp = self.proxy_opener.open('http://moth').read()
        # Get it the other way
        resp = urllib2.urlopen('http://moth').read()
        # They must be very similar
        self.assertEqual(resp, proxy_resp)
    
    def tearDown(self):
        # Shutdown the proxy server
        self._proxy.stop()
