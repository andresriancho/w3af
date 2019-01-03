"""
test_instrumented_dom_changes.py

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
import time
import Queue
import unittest

from w3af.core.controllers.chrome.tests.test_instrumented import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.instrumented import InstrumentedChrome
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestChromeCrawlerDOMChanges(unittest.TestCase):
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

    def test_onclick_change_location_detect_dom_change(self):
        """
        The goal of this test is to make sure these steps work:

            * The onclick handler in the div tag is detected
            * The div tag can be clicked
            * The browser navigates to the /a location
            * The browser detects that the click triggered a full DOM change
        """
        self._unittest_setup(TwoPagesRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

        #
        # Get event data
        #
        event_listeners = self.ic.get_html_event_listeners()
        self.assertEqual(event_listeners, [{u'tag_name': u'div',
                                            u'node_type': 1,
                                            u'selector': u'div',
                                            u'event_type': u'click',
                                            u'handler': u'goto();'}])

        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        dom_before = self.ic.get_dom()
        index_before = self.ic.get_navigation_history_index()

        #
        # Assert that navigation is not started yet
        #
        navigation_started = self.ic.navigation_started(timeout=0.5)
        self.assertFalse(navigation_started)

        #
        # Click on the div tag and force a full dom reload
        #
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))

        #
        # Navigation has started
        #
        navigation_started = self.ic.navigation_started()
        self.assertTrue(navigation_started)

        #
        # And after waiting for the page to load, it should have finished
        #
        wait_for_load = self.ic.wait_for_load()
        self.assertTrue(wait_for_load)

        navigation_started = self.ic.navigation_started()
        self.assertFalse(navigation_started)

        #
        # Assert that the event really changed the DOM
        #
        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_before, dom_after)
        self.assertEqual(dom_after, TwoPagesRequestHandler.RESPONSE_BODY_CHANGED)

        # Assert that the page changed
        index_after = self.ic.get_navigation_history_index()
        self.assertGreater(index_after, index_before)

        # Click history back and wait for load to complete
        #
        # In this step it is possible to call wait_for_load() because
        # we know that a page load will happen. After a call to dispatch_js_event()
        # the page load is only a possibility
        self.ic.navigate_to_history_index(index_before)
        self.ic.wait_for_load()

        dom_after_2 = self.ic.get_dom()

        self.assertEqual(dom_after_2, dom_before)


class TwoPagesRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY_ROOT = ('''<div onclick="goto();">This can be clicked</div>
                         
                             <script>
                                 function goto() {
                                     document.location = '/a';
                                 }                           
                             </script>''')

    RESPONSE_BODY_CHANGED = '<body><p>DOM changed</p></body>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/a':
            return 200, self.RESPONSE_BODY_CHANGED
