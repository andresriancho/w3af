"""
test_localproxy.py

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
import urllib2
import threading
import Queue
import time

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.daemons.localproxy import LocalProxy
from w3af.core.controllers.ci.moth import get_moth_http


@attr('moth')
class TestLocalProxy(unittest.TestCase):
    
    IP = '127.0.0.1'
    MOTH_MESSAGE = '<title>moth: vulnerable web application</title>'
    
    def setUp(self):
        # Start the proxy server
        create_temp_dir()

        self._proxy = LocalProxy(self.IP, 0)
        self._proxy.start()
        self._proxy.wait_for_start()
        
        port = self._proxy.get_port()

        # Build the proxy opener
        proxy_handler = urllib2.ProxyHandler({"http": "http://%s:%s"
                                              % (self.IP, port)})
        self.proxy_opener = urllib2.build_opener(proxy_handler,
                                                 urllib2.HTTPHandler)
    
    def tearDown(self):
        self._proxy.stop()
        # Not working @ CircleCI
        #self.assertNotIn(self._proxy, threading.enumerate())
        
    def test_get_thread_name(self):
        self.assertEqual(self._proxy.name, 'LocalProxyThread')
    
    def test_no_request(self):
        self.assertEqual(self._proxy.get_trapped_request(), None)
    
    def test_no_trap(self):
        self._proxy.set_trap(False)
        response = self.proxy_opener.open(get_moth_http())
        
        self.assertEqual(response.code, 200)
        
    def test_request_trapped_drop(self):
        def send_request(proxy_opener, result_queue):
            try:
                proxy_opener.open(get_moth_http())
            except urllib2.HTTPError, he:
                # Catch the 403 from the local proxy when the user
                # drops the HTTP request.
                result_queue.put(he)
        
        self._proxy.set_trap(True)
        
        result_queue = Queue.Queue()
        send_thread = threading.Thread(target=send_request, args=(self.proxy_opener,
                                                                  result_queue))
        send_thread.start()
        time.sleep(0.5)
        
        request = self._proxy.get_trapped_request()
        
        self.assertEqual(request.get_url().url_string, get_moth_http())
        self.assertEqual(request.get_method(), 'GET')
        
        self._proxy.drop_request(request)
        
        response = result_queue.get()
        
        self.assertEqual(response.code, 403)
        self.assertIn('dropped by the user', response.read())
    
    def test_request_trapped_send(self):
        def send_request(proxy_opener, result_queue):
            response = proxy_opener.open(get_moth_http())
            result_queue.put(response)
        
        self._proxy.set_trap(True)
        
        result_queue = Queue.Queue()
        send_thread = threading.Thread(target=send_request, args=(self.proxy_opener,
                                                                  result_queue))
        send_thread.start()
        time.sleep(0.5)
        
        request = self._proxy.get_trapped_request()
        
        self.assertEqual(request.get_url().url_string, get_moth_http())
        self.assertEqual(request.get_method(), 'GET')
        
        self._proxy.send_raw_request(request, request.dump_request_head(),
                                     request.get_data())
        
        response = result_queue.get()
        
        self.assertEqual(response.code, 200)
        self.assertIn(self.MOTH_MESSAGE, response.read())