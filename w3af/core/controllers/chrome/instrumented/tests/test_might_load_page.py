"""
test_might_load_page.py

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
import time

from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest
from w3af.core.controllers.chrome.instrumented.event_listener import EventListener
from w3af.core.controllers.chrome.instrumented.page_state import PageState
from w3af.core.controllers.chrome.instrumented.frame import Frame


class TestMightLoadPage(BaseInstrumentedUnittest):
    """
    This unittest asserts that all cases associated with PageState.MIGHT_NAVIGATE
    are properly working.

    In order to do this, we load a page and then dispatch an event in the
    following cases:

        * Dispatched DOM event does trigger a full DOM reload, and we assert
          that wait_for_load() and navigation_started() yield the expected
          results because page state is not PageState.MIGHT_NAVIGATE anymore.

        * Dispatched DOM event does NOT trigger a full DOM reload, and we
          want to make sure that wait_for_load() and navigation_started() yield
          the expected results here too.

    """
    def test_onclick_change_location(self):
        self._unittest_setup(TwoPagesRequestHandler)

        #
        # Get event data
        #
        event_listeners = self.ic.get_html_event_listeners()
        self.assertEqual(event_listeners, [EventListener({u'event_type': u'click',
                                                          u'tag_name': u'div',
                                                          u'handler': u'goto();',
                                                          u'node_type': 1,
                                                          u'selector': u'[onclick="goto\\(\\)\\;"]',
                                                          u'text_content': u'Thiscanbeclicked'}),
                                           EventListener({u'event_type': u'click',
                                                          u'tag_name': u'div',
                                                          u'handler': u'noop();',
                                                          u'node_type': 1,
                                                          u'selector': u'[onclick="noop\\(\\)\\;"]',
                                                          u'text_content': u'Thiscanbeclicked'})])

        # Choose the one that navigates to a different page
        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        dom_before = self.ic.get_dom()

        #
        # Assert that navigation is not started yet
        #
        navigation_started = self.ic.navigation_started(timeout=0.5)
        self.assertFalse(navigation_started)

        #
        # Click on the div tag and force a full dom reload, this will set the
        # page state to MIGHT_NAVIGATE (at least for 1ms) and then it will
        # switch to PAGE_STATE_LOADING
        #
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))
        self.assertIn(self.ic.page_state.get(), [PageState.MIGHT_NAVIGATE,
                                                 PageState.STATE_LOADING])

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
        # And the page state must be STATE_LOADED
        #
        self.assertEqual(self.ic.page_state.get(), PageState.STATE_LOADED)

        #
        # Assert that the event really changed the DOM
        #
        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_before, dom_after)
        self.assertEqual(dom_after, TwoPagesRequestHandler.RESPONSE_BODY_CHANGED)

    def test_onclick_noop(self):
        self._unittest_setup(TwoPagesRequestHandler)

        #
        # Get event data
        #
        event_listeners = self.ic.get_html_event_listeners()
        self.assertEqual(event_listeners, [EventListener({u'event_type': u'click',
                                                          u'tag_name': u'div',
                                                          u'handler': u'goto();',
                                                          u'node_type': 1,
                                                          u'selector': u'[onclick="goto\\(\\)\\;"]',
                                                          u'text_content': u'Thiscanbeclicked'}),
                                           EventListener({u'event_type': u'click',
                                                          u'tag_name': u'div',
                                                          u'handler': u'noop();',
                                                          u'node_type': 1,
                                                          u'selector': u'[onclick="noop\\(\\)\\;"]',
                                                          u'text_content': u'Thiscanbeclicked'})])

        # Choose the one that does nothing, no new navigation is started
        event_listener = event_listeners[1]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        dom_before = self.ic.get_dom()

        #
        # Assert that navigation is not started
        #
        navigation_started = self.ic.navigation_started(timeout=0.5)
        self.assertFalse(navigation_started)

        #
        # Click on the div tag, this will do nothing in the browser but we'll
        # set the page state to MIGHT_NAVIGATE because we have no way of
        # knowing beforehand
        #
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))
        self.assertEqual(self.ic.page_state.get(), PageState.MIGHT_NAVIGATE)

        #
        # Navigation has not started
        #
        navigation_started = self.ic.navigation_started(timeout=0.5)
        self.assertFalse(navigation_started)

        #
        # We can wait for a page load, but it will return False because there
        # is no page being loaded
        #
        wait_for_load = self.ic.wait_for_load(timeout=0.5)
        self.assertFalse(wait_for_load)

        #
        # And the page state is still MIGHT_NAVIGATE
        #
        self.assertEqual(self.ic.page_state.get(), PageState.MIGHT_NAVIGATE)

        #
        # Assert that the event never changed the DOM
        #
        dom_after = self.ic.get_dom()
        self.assertEqual(dom_before, dom_after)

        #
        # After some time the InstrumentedChrome realizes that the JS code will
        # not actually navigate, so it changes the page state to STATE_LOADED
        #
        time.sleep(Frame.MAX_SECONDS_IN_MIGHT_NAVIGATE)

        self.assertEqual(self.ic.page_state.get(), PageState.STATE_LOADED)


class TwoPagesRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY_ROOT = ('''<div onclick="goto();">This can be clicked</div>
    
                             <div onclick="noop();">This can be clicked</div>

                             <script>
                                 function goto() {
                                     document.location = '/a';
                                 }
                                 
                                 function noop() {
                                     console.log("nothing");
                                 }                                                      
                             </script>''')

    RESPONSE_BODY_CHANGED = u'<html><head></head><body><p>DOM changed</p></body></html>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/a':
            return 200, self.RESPONSE_BODY_CHANGED
