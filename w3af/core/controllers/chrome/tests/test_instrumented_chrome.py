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
import os
import ssl
import Queue
import unittest
import BaseHTTPServer

from w3af import ROOT_PATH
from w3af.core.controllers.chrome.instrumented_chrome import InstrumentedChrome
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.url.tests.helpers.ssl_daemon import SSLServer


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
        self.start_and_load(url)

    def test_start_and_load_https_self_signed(self):
        # Define the HTTP response
        http_response = ('HTTP/1.1 200 Ok\r\n'
                         'Connection: close\r\n'
                         'Content-Type: text/html\r\n'
                         'Content-Length: %s\r\n\r\n%s')

        body = InstrumentedChromeHandler.RESPONSE_BODY
        http_response %= (len(body), body)

        # Start the HTTPS server
        cert = os.path.join(ROOT_PATH, 'plugins', 'tests', 'audit', 'certs', 'invalid_cert.pem')
        s = SSLServer(self.SERVER_HOST, 0, cert, http_response=http_response)

        s.start()
        s.wait_for_start()

        server_port = s.get_port()
        url = 'https://%s:%s/' % (self.SERVER_HOST, server_port)

        self.start_and_load(url)

        s.stop()

    def start_and_load(self, url):
        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), InstrumentedChromeHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), InstrumentedChromeHandler.RESPONSE_BODY)
        self.assertIn('Chrome', request.get_headers().get('User-agent'))

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
