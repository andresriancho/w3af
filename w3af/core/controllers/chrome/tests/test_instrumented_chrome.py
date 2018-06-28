"""
test_instrumented_chrome.py

Copyright 2018 Andres Riancho

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
import Queue
import unittest
import BaseHTTPServer

from w3af.core.controllers.chrome.instrumented_chrome import InstrumentedChrome
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestInstrumentedChrome(unittest.TestCase):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        self.server, self.server_port = start_webserver_any_free_port(self.SERVER_HOST,
                                                                      webroot=self.SERVER_ROOT_PATH,
                                                                      handler=InstrumentedChromeHandler)

        self.ic = InstrumentedChrome(self.uri_opener, self.http_traffic_queue)

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        self.ic.terminate()

    def test_start_and_load_http(self):
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), InstrumentedChromeHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), InstrumentedChromeHandler.RESPONSE_BODY)
        self.assertIn('Chrome', request.get_headers().get('User-agent'))

    def test_start_and_load_https_self_signed(self):
        raise NotImplementedError

    def test_chrome_fails_to_start(self):
        raise NotImplementedError

    def test_initial_connection_to_chrome_fails(self):
        raise NotImplementedError

    def test_connection_to_chrome_fails_after_page_load(self):
        raise NotImplementedError

    def test_proxy_fails_to_start(self):
        raise NotImplementedError

    def test_proxy_dies(self):
        raise NotImplementedError


class InstrumentedChromeHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    RESPONSE_BODY = '<body>Hello world</body>'

    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.RESPONSE_BODY)
        except Exception, e:
            print('[InstrumentedChromeHandler] Exception: "%s".' % e)
        finally:
            # Clean up
            self.close_connection = 1
            self.rfile.close()
            self.wfile.close()
            return

    def log_message(self, fmt, *args):
        """
        I dont want messages to be written to stderr, please ignore them.

        If I don't override this method I end up with messages like:
        eulogia.local - - [19/Oct/2012 10:12:33] "GET /GGC8s1dk HTTP/1.0" 200 -

        being printed to the console.
        """
        pass
