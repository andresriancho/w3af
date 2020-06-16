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
import Queue
import unittest

from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.tests.helpers import set_debugging_in_output_manager
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class BaseInstrumentedUnittest(unittest.TestCase):
    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def setUp(self):
        set_debugging_in_output_manager()

        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        self.ic = None
        self.server = None
        self.server_thread = None

    def _unittest_setup(self, request_handler_klass, load_url=True):
        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

        self.server_thread = t
        self.server = s
        self.server_port = p

        self.ic = InstrumentedChrome(self.uri_opener, self.http_traffic_queue)

        if load_url:
            url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
            self.ic.load_url(url)
            self.ic.wait_for_load()

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        if self.ic is not None:
            if self.ic.chrome_conn is not None:
                if self.ic.chrome_conn.ws.connected:
                    self.assertEqual(self.ic.get_js_errors(), [])
            self.ic.terminate()

        if self.server is not None:
            self.server.shutdown()

        if self.server_thread is not None:
            self.server_thread.join()

    def _print_all_console_messages(self):
        for console_message in self.ic.get_console_messages():
            print(console_message)
