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
import time

from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.instrumented.tests.test_instrumented_event_listeners import (EventListenerInDocument,
                                                                                               EventListenerInWindow)


class TestChromeCrawlerDispatchEvents(BaseInstrumentedUnittest):
    def test_dispatch_click_event(self):
        self._unittest_setup(OnClickEventRequestHandler)

        # The event was recorded
        event_listeners = self.ic.get_js_event_listeners()

        self.assertEqual(event_listeners, [{u'use_capture': False,
                                            u'tag_name': u'table',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'#outside',
                                            u'text_content': u'onetwo'}])

        dom_before = self.ic.get_dom()

        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        # dispatch the event
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))

        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_after, dom_before)
        self.assertIn('<td id="t2">three</td>', dom_after)
        self.assertNotIn('<td id="t2">two</td>', dom_after)

        self.assertIn('<td id="t2">two</td>', dom_before)
        self.assertNotIn('<td id="t2">three</td>', dom_before)

        # The event is still in there
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'use_capture': False,
                                                             u'tag_name': u'table',
                                                             u'event_type': u'click',
                                                             u'node_type': 1,
                                                             u'selector': u'#outside',
                                                             u'text_content': u'onetwo'}])

    def test_dispatch_click_event_is_async(self):
        self._unittest_setup(OnClickEventTimeoutRequestHandler)

        # The event was recorded
        event_listeners = self.ic.get_js_event_listeners()
        self.assertEqual(event_listeners, [{u'use_capture': False,
                                            u'tag_name': u'table',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'#outside',
                                            u'text_content': u'onetwo'}])

        dom_before = self.ic.get_dom()

        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        # dispatch the event
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))

        # note that the event is dispatched in an async way, so the
        # dispatch_js_event() call will never timeout, even when the
        # handler(s) for that event take a lot of time to run
        dom_after = self.ic.get_dom()

        self.assertEqual(dom_after, dom_before)

        # sleep to give the event handler time to work
        time.sleep(11)

        # and now the changes were applied
        dom_after = self.ic.get_dom()
        self.assertNotEqual(dom_after, dom_before)

        self.assertIn('<td id="t2">three</td>', dom_after)
        self.assertNotIn('<td id="t2">two</td>', dom_after)

        self.assertIn('<td id="t2">two</td>', dom_before)
        self.assertNotIn('<td id="t2">three</td>', dom_before)

        # The event is still in there
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'use_capture': False,
                                                             u'tag_name': u'table',
                                                             u'event_type': u'click',
                                                             u'node_type': 1,
                                                             u'selector': u'#outside',
                                                             u'text_content': u'onetwo'}])

    def test_dispatch_click_event_to_document(self):
        self._unittest_setup(EventListenerInDocument)

        # The event was recorded
        event_listeners = self.ic.get_js_event_listeners()

        self.assertEqual(event_listeners, [{u'event_type': u'click',
                                            u'tag_name': u'!document',
                                            u'node_type': 9,
                                            u'selector': u'!document'}])

        dom_before = self.ic.get_dom()

        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        # dispatch the event
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))

        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_after, dom_before)
        self.assertIn('Hello World!2', dom_after)

        # The event is still in there
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'event_type': u'click',
                                                             u'tag_name': u'!document',
                                                             u'node_type': 9,
                                                             u'selector': u'!document'}])

    def test_dispatch_click_event_to_window(self):
        self._unittest_setup(EventListenerInWindow)

        # The event was recorded
        event_listeners = self.ic.get_js_event_listeners()

        self.assertEqual(event_listeners, [{u'event_type': u'click',
                                            u'tag_name': u'!window',
                                            u'node_type': -1,
                                            u'selector': u'!window'}])

        dom_before = self.ic.get_dom()

        event_listener = event_listeners[0]
        selector = event_listener['selector']
        event_type = event_listener['event_type']

        # dispatch the event
        self.assertTrue(self.ic.dispatch_js_event(selector, event_type))

        dom_after = self.ic.get_dom()

        self.assertNotEqual(dom_after, dom_before)
        self.assertIn('Hello World!2', dom_after)

        # The event is still in there
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'event_type': u'click',
                                                             u'tag_name': u'!window',
                                                             u'node_type': -1,
                                                             u'selector': u'!window'}])


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


class OnClickEventTimeoutRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    #
    # This code works: tested directly in Google Chrome. The text is changed
    # after the specified delay.
    RESPONSE_BODY = ('''<table id="outside">
                            <tr><td id="t1">one</td></tr>
                            <tr><td id="t2">two</td></tr>
                        </table>

                        <script>
                            function sleep(ms) {
                                return new Promise(resolve => setTimeout(resolve, ms));
                            }

                            // Function to change the content of t2
                            async function modifyText() {                              
                                await sleep(1000 * 10);
                               
                                var t2 = document.getElementById("t2");
                                if (t2.firstChild.nodeValue == "three") {
                                    t2.firstChild.nodeValue = "two";
                                } else {
                                    t2.firstChild.nodeValue = "three";
                                }
                              
                                // Added this long sleep here
                                await sleep(1000 * 10);
                            }

                            // add event listener to table
                            var el = document.getElementById("outside");
                            el.addEventListener("click", modifyText, false);
                        </script>
                        ''')

