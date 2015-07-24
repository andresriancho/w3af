"""
test_intercept_proxy.py

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
import threading
import unittest
import urllib2
import Queue
import time

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.daemons.proxy import InterceptProxy
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.url.extended_urllib import ExtendedUrllib


@attr('moth')
class TestInterceptProxy(unittest.TestCase):
    
    IP = '127.0.0.2'
    MOTH_MESSAGE = '<title>moth: vulnerable web application</title>'
    PAGE_NOT_FOUND = 'Page not found'
    
    def setUp(self):
        # Start the proxy server
        create_temp_dir()

        self._proxy = InterceptProxy(self.IP, 0, ExtendedUrllib())
        self._proxy.start()
        self._proxy.wait_for_start()

        port = self._proxy.get_port()

        # Build the proxy opener
        proxy_url = 'http://%s:%s' % (self.IP, port)
        proxy_handler = urllib2.ProxyHandler({'http': proxy_url,
                                              'https': proxy_url})
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

        self.assertIn(self.MOTH_MESSAGE, response.read())
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
        
        self.assertEqual(request.get_uri().url_string, get_moth_http())
        self.assertEqual(request.get_method(), 'GET')
        
        self._proxy.drop_request(request)
        
        response = result_queue.get()
        
        self.assertEqual(response.code, 403)
        self.assertIn('HTTP request drop by user', response.read())
    
    def test_request_trapped_send(self):
        def send_request(proxy_opener, result_queue):
            try:
                response = proxy_opener.open(get_moth_http())
            except urllib2.HTTPError, he:
                # Catch the 403 from the local proxy when the user
                # drops the HTTP request.
                result_queue.put(he)
            else:
                result_queue.put(response)

        self._proxy.set_trap(True)
        
        result_queue = Queue.Queue()
        send_thread = threading.Thread(target=send_request, args=(self.proxy_opener,
                                                                  result_queue))
        send_thread.start()
        time.sleep(0.5)
        
        request = self._proxy.get_trapped_request()
        
        self.assertEqual(request.get_uri().url_string, get_moth_http())
        self.assertEqual(request.get_method(), 'GET')
        
        self._proxy.on_request_edit_finished(request,
                                             request.dump_request_head(),
                                             request.get_data())
        
        response = result_queue.get()
        
        self.assertEqual(response.code, 200)
        self.assertIn(self.MOTH_MESSAGE, response.read())

    def test_trap_many(self):
        def send_request(_id, proxy_opener, results, exceptions):
            url = get_moth_http('/%s' % _id)

            try:
                response = proxy_opener.open(url, timeout=10)
            except urllib2.HTTPError, he:
                # Catch the 403 from the local proxy when the user
                # drops the HTTP request.
                results.put(he)
            except KeyboardInterrupt, k:
                exceptions.put(k)
            except Exception, e:
                exceptions.put(e)
            else:
                results.put(response)

        self._proxy.set_trap(True)

        result_queue = Queue.Queue()
        exceptions_queue = Queue.Queue()

        for i in xrange(3):
            args = (i, self.proxy_opener, result_queue, exceptions_queue)
            send_thread = threading.Thread(target=send_request, args=args)
            send_thread.start()
            time.sleep(1)

        #
        # The UI gets the first trapped request and processes it:
        #
        self.assertNoExceptionInQueue(exceptions_queue)
        request = self._proxy.get_trapped_request()

        self.assertIsNotNone(request, 'The proxy did not receive request 0')

        self.assertEqual(request.get_uri().url_string, get_moth_http('/0'))
        self.assertEqual(request.get_method(), 'GET')

        # It doesn't modify it
        self._proxy.on_request_edit_finished(request,
                                             request.dump_request_head(),
                                             request.get_data())

        # And we get the corresponding response
        response = result_queue.get()

        self.assertEqual(response.geturl(), get_moth_http('/0'))
        self.assertEqual(response.code, 404)
        self.assertIn(self.PAGE_NOT_FOUND, response.read())

        #
        # The UI gets the second trapped request and processes it:
        #
        self.assertNoExceptionInQueue(exceptions_queue)
        request = self._proxy.get_trapped_request()

        self.assertIsNotNone(request, 'The proxy did not receive request 1')

        self.assertEqual(request.get_uri().url_string, get_moth_http('/1'))
        self.assertEqual(request.get_method(), 'GET')

        # It drops the request
        self._proxy.drop_request(request)

        # And we get the corresponding response
        response = result_queue.get()

        self.assertEqual(response.geturl(), get_moth_http('/1'))
        self.assertEqual(response.code, 403)

        #
        # The UI gets the third trapped request and processes it:
        #
        self.assertNoExceptionInQueue(exceptions_queue)
        request = self._proxy.get_trapped_request()

        self.assertIsNotNone(request, 'The proxy did not receive request 2')

        self.assertEqual(request.get_uri().url_string, get_moth_http('/2'))
        self.assertEqual(request.get_method(), 'GET')

        # It doesn't modify it
        self._proxy.on_request_edit_finished(request,
                                             request.dump_request_head(),
                                             request.get_data())

        # And we get the corresponding response
        response = result_queue.get()

        self.assertEqual(response.geturl(), get_moth_http('/2'))
        self.assertEqual(response.code, 404)
        self.assertIn(self.PAGE_NOT_FOUND, response.read())

    def assertNoExceptionInQueue(self, exceptions_queue):
        try:
            exception = exceptions_queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            self.assertIsNone(exception)