"""
test_proxy.py

Copyright 2019 Andres Riancho

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
import os
import time
import Queue
import urllib2
import unittest
import subprocess

from multiprocessing.pool import ThreadPool

from w3af.core.controllers.chrome.proxy.main import LoggingProxy
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestProxy(unittest.TestCase):
    def setUp(self):
        self._uri_opener = ExtendedUrllib()
        self._http_traffic_queue = Queue.Queue()

        self.proxy = LoggingProxy('127.0.0.1',
                                  0,
                                  self._uri_opener,
                                  name='ChromeProxy',
                                  queue=self._http_traffic_queue)

        self.proxy.set_debugging_id('0xd3adb33f')

        self.proxy.start()
        self.proxy.wait_for_start()

    def test_proxy_basic_request(self):
        # Setup the opener
        proxy = urllib2.ProxyHandler({'http': '127.0.0.1:%s' % self.proxy.get_bind_port()})
        opener = urllib2.build_opener(proxy)

        #
        # Send the request via proxy and time it
        #
        start = time.time()
        response = opener.open('https://en.wikipedia.org/wiki/Cross-site_scripting')
        response.read()
        spent_via_proxy = time.time() - start

        #
        # Send the request without the proxy and time it
        #
        start = time.time()
        response = urllib2.urlopen('https://en.wikipedia.org/wiki/Cross-site_scripting')
        response.read()
        spent_no_proxy = time.time() - start

        # print('Time with proxy: %.2f' % spent_via_proxy)
        # print('Time without proxy: %.2f' % spent_no_proxy)
        self.assertLess(spent_via_proxy, spent_no_proxy * 1.05)

    def test_no_connections_in_close_wait(self):
        processes = 100
        http_requests = processes * 4

        # Setup the opener
        proxy = urllib2.ProxyHandler({'http': '127.0.0.1:%s' % self.proxy.get_bind_port()})
        opener = urllib2.build_opener(proxy)

        pool = ThreadPool(processes=processes)

        def open_read(url):
            response = opener.open(url)
            response.read()

        args = ['https://en.wikipedia.org/wiki/Cross-site_scripting'] * http_requests
        pool.map(open_read, args)

        pool.close()
        pool.join()

        cmd = 'lsof -n -p %s 2>&1' % os.getpid()
        lsof = subprocess.check_output(cmd, shell=True)

        self.assertNotIn('CLOSE_WAIT', lsof)
