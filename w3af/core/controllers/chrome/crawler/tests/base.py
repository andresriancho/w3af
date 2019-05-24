"""
base.py

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
import unittest

from w3af.core.controllers.output_manager import manager
from w3af.core.controllers.chrome.tests.helpers import set_debugging_in_output_manager
from w3af.core.controllers.chrome.crawler.main import ChromeCrawler
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class BaseChromeCrawlerTest(unittest.TestCase):
    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def setUp(self):
        if int(os.getenv('CHROME_DEBUG', 0)) == 1:
            set_debugging_in_output_manager()

        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()
        self.crawler = ChromeCrawler(self.uri_opener)

    def _unittest_setup(self, request_handler_klass):
        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

        self.server_thread = t
        self.server = s
        self.server_port = p

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get_nowait()

        self.crawler.terminate()
        self.server.shutdown()
        self.server_thread.join()

        self._wait_for_output_manager_messages()

    def _wait_for_output_manager_messages(self):
        start = time.time()

        while not manager.in_queue.empty():
            time.sleep(0.1)
            spent = time.time() - start

            if spent > 2.0:
                break
