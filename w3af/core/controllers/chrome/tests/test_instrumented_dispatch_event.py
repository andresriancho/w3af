"""
test_instrumented_dispatch_event.py

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


class TestChromeCrawlerDispatchEvents(unittest.TestCase):
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

    def test_dispatch_click_event(self):
        self._unittest_setup(OnClickEventRequestHandler)

        # The event was recorded
        self.assertEqual(self.ic.get_js_event_listeners(), [[{}, u'click', {}, False]])

        dom_before = self.ic.get_dom()

        # dispatch the event
        self.ic.dispatch_js_event(0)

        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_after, dom_before)
        self.assertIn('<td id="t2">three</td>', dom_after)
        self.assertNotIn('<td id="t2">two</td>', dom_after)

        self.assertIn('<td id="t2">two</td>', dom_before)
        self.assertNotIn('<td id="t2">three</td>', dom_before)

        # The event is still in there
        self.assertEqual(self.ic.get_js_event_listeners(), [[{}, u'click', {}, False]])


class OnClickEventRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<table id="outside">
                            <tr><td id="t1">one</td></tr>
                            <tr><td id="t2">two</td></tr>
                        </table>

                        <script>
                            // Function to change the content of t2
                            function modifyText() {
                              var t2 = document.getElementById("t2");
                              if (t2.firstChild.nodeValue == "three") {
                                t2.firstChild.nodeValue = "two";
                              } else {
                                t2.firstChild.nodeValue = "three";
                              }
                            }

                            // add event listener to table
                            var el = document.getElementById("outside");
                            el.addEventListener("click", modifyText, false);
                        </script>
                        ''')

