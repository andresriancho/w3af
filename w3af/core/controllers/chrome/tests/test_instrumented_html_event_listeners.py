"""
test_instrumented_html_event_listeners.py

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

from w3af.core.controllers.chrome.tests.test_instrumented import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.instrumented import InstrumentedChrome
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestChromeCrawlerGetHTMLEventListeners(unittest.TestCase):
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

        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.ic.load_url(url)

        self.ic.wait_for_load()

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        self.assertEqual(self.ic.get_js_errors(), [])

        self.ic.terminate()
        self.server.shutdown()
        self.server_thread.join()

    def _print_all_console_messages(self):
        for console_message in self.ic.get_console_messages():
            print(console_message)

    def test_no_event_handlers_empty(self):
        self._unittest_setup(EmptyRequestHandler)
        self.assertEqual(self.ic.get_html_event_listeners(), [])

    def test_no_event_handlers_link(self):
        self._unittest_setup(LinkTagRequestHandler)
        self.assertEqual(self.ic.get_html_event_listeners(), [])

    def test_onclick_event_listener(self):
        self._unittest_setup(OnClickEventRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()
        self._print_all_console_messages()
        self.assertEqual(event_listeners, [{u'events': [{u'event': u'onclick',
                                                         u'handler': u'modifyText();'}],
                                            u'selector': u'#outside',
                                            u'tag_name': u'table'}])


class EmptyRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ''


class LinkTagRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<a href="/">click</a>'


class OnClickEventRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<table id="outside" onclick="modifyText();">
                            <tr><td id="t1">one</td></tr>
                            <tr><td id="t2">two</td></tr>
                        </table>

                        <script>
                            // Function to change the content of t2
                            function modifyText(e) {
                              e.preventDefault();
                              
                              var t2 = document.getElementById("t2");
                              if (t2.firstChild.nodeValue == "three") {
                                t2.firstChild.nodeValue = "two";
                              } else {
                                t2.firstChild.nodeValue = "three";
                              }
                            }
                        </script>
                        ''')
