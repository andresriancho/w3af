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

from urlparse import urlparse

from websocket import WebSocketConnectionClosedException

from w3af import ROOT_PATH
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.instrumented.exceptions import InstrumentedChromeException
from w3af.core.controllers.chrome.devtools import ChromeInterfaceException
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest
from w3af.core.data.url.tests.helpers.ssl_daemon import SSLServer


class TestInstrumentedChrome(BaseInstrumentedUnittest):

    def test_terminate(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        self.ic.terminate()

    def test_start_and_load_http(self):
        self._unittest_setup(ExtendedHttpRequestHandler, load_url=False)

        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))

    def test_load_about_blank(self):
        self._unittest_setup(ExtendedHttpRequestHandler, load_url=False)
        self.ic.load_about_blank()
        self.assertEqual(self.http_traffic_queue.qsize(), 0)

    def test_get_pid(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        pid = self.ic.get_pid()
        self.assertIsInstance(pid, (int, long))

    def test_get_memory_usage(self):
        self._unittest_setup(ExtendedHttpRequestHandler)
        private, shared = self.ic.get_memory_usage()
        self.assertIsInstance(private, int)
        self.assertIsInstance(shared, int)

    def test_start_and_load_https_self_signed(self):
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

        self.ic = InstrumentedChrome(self.uri_opener, self.http_traffic_queue)

        self.ic.load_url(url)
        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), ExtendedHttpRequestHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))

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


class TestInstrumentedChromeWithDialogDismiss(BaseInstrumentedUnittest):

    def test_load_page_with_alert(self):
        self._unittest_setup(CreateAlertHandler)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.ic.load_url(url)

        self.ic.wait_for_load()

        self.assertEqual(self.ic.get_dom(), CreateAlertHandler.RESPONSE_BODY)
        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        #
        # The first request / response
        #
        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), CreateAlertHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))

        #
        # The second request / response
        #
        request, response = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)
        self.assertEqual(response.get_url().url_string, url)

        self.assertEqual(response.get_body(), CreateAlertHandler.RESPONSE_BODY)
        self.assertIn('Mozilla/', request.get_headers().get('User-agent'))


class TestInstrumentedChromeWith401(BaseInstrumentedUnittest):

    def test_load_page_with_401(self):
        # It is possible to load a URL that returns a 401 and then load
        # any other URL in the same browser instance
        self._unittest_setup(BasicAuthRequestHandler, load_url=False)
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


class TestInstrumentedChromeWith301Redirect(BaseInstrumentedUnittest):

    def test_load_page_with_redirect_301(self):
        self._unittest_setup(RedirectRequestHandler, load_url=False)
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        # Just load the URL and assert that no exceptions were raised
        self.ic.load_url(url)
        self.ic.wait_for_load()


class TestInstrumentedChromeReadJSVariables(BaseInstrumentedUnittest):

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
    RESPONSE_BODY = '<html><head><script>alert(1);</script></head><body></body></html>'


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


class RedirectRequestHandler(ExtendedHttpRequestHandler):

    SUCCESS = u'<html><head></head><body>Hello world</body></html>'

    def do_GET(self):
        request_path = urlparse(self.path).path

        if request_path == '/':
            code = 301
            body = ''
            headers = {
                'Location': '/redirected',
            }

        elif request_path == '/redirected':
            code = 200
            body = RedirectRequestHandler.SUCCESS
            headers = {
                'Content-Type': 'text/html',
                'Content-Length': len(body),
                'Content-Encoding': 'identity'
            }

        else:
            code = 404
            body = 'Not found'
            headers = {
                'Content-Type': 'text/html',
                'Content-Length': len(body),
                'Content-Encoding': 'identity'
            }

        self.send_response_to_client(code, body, headers)
