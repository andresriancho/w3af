"""
test_instrumented.py

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
import Queue
import unittest

from websocket import WebSocketConnectionClosedException

from w3af import ROOT_PATH
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.instrumented.exceptions import InstrumentedChromeException
from w3af.core.controllers.chrome.devtools import ChromeInterfaceException
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.url.tests.helpers.ssl_daemon import SSLServer


class InstrumentedChromeUnittest(unittest.TestCase):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def _unittest_setup(self, request_handler_klass):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

        self.server_thread = t
        self.server = s
        self.server_port = p

        self.ic = InstrumentedChrome(self.uri_opener, self.http_traffic_queue)

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        self.ic.terminate()
        self.server.shutdown()
        self.server_thread.join()

    def start_and_load(self, url):
        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))


class TestInstrumentedChrome(InstrumentedChromeUnittest):

    def test_terminate(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        self.ic.terminate()

    def test_start_and_load_http(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.start_and_load(url)

    def test_load_about_blank(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        self.ic.load_about_blank()
        self.assertEqual(self.http_traffic_queue.qsize(), 0)

    def test_get_pid(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        pid = self.ic.get_pid()
        self.assertIsInstance(pid, int)

    def test_get_memory_usage(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        private, shared = self.ic.get_memory_usage()
        self.assertIsInstance(private, int)
        self.assertIsInstance(shared, int)

    def test_start_and_load_https_self_signed(self):
        self._unittest_setup(ExtendedHttpRequestHandler)

        # Define the HTTP response
        http_response = ('HTTP/1.1 200 Ok\r\n'
                         'Connection: close\r\n'
                         'Content-Type: text/html\r\n'
                         'Content-Length: %s\r\n\r\n%s')

        body = ExtendedHttpRequestHandler.RESPONSE_BODY
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

    def test_initial_connection_to_chrome_fails(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        self.ic.chrome_process.get_devtools_port = lambda: 1
        self.assertRaises(InstrumentedChromeException, self.ic.connect_to_chrome)

    def test_connection_to_chrome_fails_after_page_load(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.ic.load_url(url)
        self.ic.wait_for_load()

        # We simulate an error here
        self.ic.chrome_conn.ws.close()

        # Trigger it here
        self.assertRaises(WebSocketConnectionClosedException, self.ic.load_url, url)

    def test_proxy_dies(self):
        self._unittest_setup(ExtendedHttpRequestHandler)

        # We simulate an error here
        self.ic.proxy.stop()

        # Exception is raised
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.assertRaises(ChromeInterfaceException, self.ic.load_url, url)

    def test_exception_handling_in_custom_handlers(self):
        self._unittest_setup(ExtendedHttpRequestHandler)

        class UnittestException(Exception):
            pass

        def raises_exception(message):
            raise UnittestException('unittest')

        self.ic.chrome_conn.set_event_handler(raises_exception)

        # Exception is raised!
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.assertRaises(UnittestException, self.ic.load_url, url)

        # If we remove the buggy handler things work again
        self.ic.chrome_conn.unset_event_handler(raises_exception)

        self.ic.load_url(url)
        self.ic.wait_for_load()
        self.assertEqual(self.ic.get_dom(), ExtendedHttpRequestHandler.RESPONSE_BODY)

    def test_websocket_call_triggers_error_in_chrome(self):
        self._unittest_setup(ExtendedHttpRequestHandler)

        self.assertRaises(ChromeInterfaceException,
                          self.ic.navigate_to_history_index, 300)


class TestInstrumentedChromeWithDialogDismiss(InstrumentedChromeUnittest):

    def test_load_page_with_alert(self):
        self._unittest_setup(CreateAlertHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), u'<body></body>')
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), CreateAlertHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))


class TestInstrumentedChromeWith401(InstrumentedChromeUnittest):

    def test_load_page_with_401(self):
        # It is possible to load a URL that returns a 401 and then load
        # any other URL in the same browser instance
        self._unittest_setup(BasicAuthRequestHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        #
        # Load the first URL
        #
        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), BasicAuthRequestHandler.BASIC_AUTH)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), BasicAuthRequestHandler.BASIC_AUTH)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))

        #
        # Load the second URL
        #
        self.ic.load_url(url + 'success')
        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), BasicAuthRequestHandler.SUCCESS)


class TestInstrumentedChromeReadJSVariables(InstrumentedChromeUnittest):

    def test_load_page_read_js_variable(self):
        self._unittest_setup(JSVariablesHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.ic.load_url(url)
        self.ic.wait_for_load()

        # all of these work
        self.assertEqual(self.ic.get_js_variable_value('foo'), {'bar': 'baz'})
        self.assertEqual(self.ic.get_js_variable_value('window.window.foo'), {'bar': 'baz'})
        self.assertEqual(self.ic.get_js_variable_value('window.foo'), {'bar': 'baz'})


class CreateAlertHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<script>alert(1);</script>'


class BasicAuthRequestHandler(ExtendedHttpRequestHandler):

    SUCCESS = u'<html><head></head><body>Hello world</body></html>'
    BASIC_AUTH = u'<html><head></head><body></body></html>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 401, self.BASIC_AUTH
        elif request_path == '/success':
            return 200, self.SUCCESS


class JSVariablesHandler(ExtendedHttpRequestHandler):

    RESPONSE_BODY = ('<script>'
                     '    window.foo = {'
                     '        "bar" : "baz"'
                     '    }'
                     '</script>')
