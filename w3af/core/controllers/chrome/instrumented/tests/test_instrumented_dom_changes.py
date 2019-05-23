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
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler


class TestChromeCrawlerDOMChanges(BaseInstrumentedUnittest):
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
                                            u'selector': u'[onclick]',
                                            u'event_type': u'click',
                                            u'handler': u'goto();',
                                            u'text_content': u'Thiscanbeclicked'}])

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

        wait_for_load = self.ic.wait_for_load()
        self.assertTrue(wait_for_load)

        dom_after_2 = self.ic.get_dom()

        self.assertEqual(dom_after_2, dom_before)


class TwoPagesRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY_ROOT = ('''<div onclick="goto();">This can be clicked</div>
                         
                             <script>
                                 function goto() {
                                     document.location = '/a';
                                 }                           
                             </script>''')

    RESPONSE_BODY_CHANGED = u'<html><head></head><body><p>DOM changed</p></body></html>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/a':
            return 200, self.RESPONSE_BODY_CHANGED
