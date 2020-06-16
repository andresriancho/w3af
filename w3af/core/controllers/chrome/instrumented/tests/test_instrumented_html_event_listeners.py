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
import pprint

from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.instrumented.paginate import PAGINATION_PAGE_COUNT
from w3af.core.controllers.chrome.instrumented.tests.test_instrumented_event_listeners import OnClickEventSetOnClickRequestHandler
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest


class TestChromeCrawlerGetHTMLEventListeners(BaseInstrumentedUnittest):
    def test_no_event_handlers_empty(self):
        self._unittest_setup(EmptyRequestHandler)
        self.assertEqual(self.ic.get_html_event_listeners(), [])

    def test_no_event_handlers_link(self):
        self._unittest_setup(LinkTagRequestHandler)
        self.assertEqual(self.ic.get_html_event_listeners(), [])

    def test_onclick_event_listener_invisible_table(self):
        self._unittest_setup(OnClickEventInvisibleTableRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(event_listeners, [])

    def test_onclick_event_set_attribute(self):
        self._unittest_setup(OnClickEventSetOnClickRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()
        self._print_all_console_messages()

        self.assertEqual(event_listeners, [{u'event_type': u'click',
                                            u'tag_name': u'table',
                                            u'node_type': 1,
                                            u'selector': u'#outside',
                                            u'text_content': u'onetwo',
                                            u'event_source': u'property'}])

    def test_onclick_event_listener_children_that_do_not_inherit(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(event_listeners, [{u'tag_name': u'table',
                                            u'handler': u'modifyText();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'[onclick]',
                                            u'text_content': u'one',
                                            u'event_source': u'attribute'}])

    def test_html_events_filter_out_click(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(event_filter=['foobar'])

        self.assertEqual(event_listeners, [])

    def test_html_events_filter_in_click(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(event_filter=['click'])

        self.assertEqual(event_listeners, [{u'tag_name': u'table',
                                            u'handler': u'modifyText();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'[onclick]',
                                            u'text_content': u'one',
                                            u'event_source': u'attribute'}])

    def test_html_events_filter_out_table(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(tag_name_filter=['foobar'])

        self.assertEqual(event_listeners, [])

    def test_html_events_filter_in_table(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(tag_name_filter=['table'])

        self.assertEqual(event_listeners, [{u'tag_name': u'table',
                                            u'handler': u'modifyText();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'[onclick]',
                                            u'text_content': u'one',
                                            u'event_source': u'attribute'}])

    def test_onclick_event_listener_with_children(self):
        self._unittest_setup(OnClickEventWithChildrenRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()
        self.maxDiff = None
        expected = [{u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'[onclick]',
                     u'tag_name': u'div',
                     u'text_content': u'Allowedtoclick1Allowedtoclick2',
                     u'event_source': u'attribute'},
                    {u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'[id="1"]',
                     u'tag_name': u'span',
                     u'text_content': u'Allowedtoclick1',
                     u'event_source': u'attribute'},
                    {u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'[id="2"]',
                     u'tag_name': u'span',
                     u'text_content': u'Allowedtoclick2',
                     u'event_source': u'attribute'}]

        self.assertEqual(event_listeners, expected)

    def test_two_onclick(self):
        self._unittest_setup(TwoOnClickRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        # Note: The HTML has two onclick attributes. Chrome (checked with the
        #       real browser devtools) will only use the second one. The first
        #       is lost during some parsing / DOM generation function inside
        #       chrome
        self.assertEqual(event_listeners, [{u'tag_name': u'div',
                                            u'handler': u'def();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'[onclick]',
                                            u'text_content': u'x',
                                            u'event_source': u'attribute'}])

    def test_events_less_than_count(self):
        self._unittest_setup(EventsLessThanCountHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(len(event_listeners),
                         PAGINATION_PAGE_COUNT - 1,
                         event_listeners)

    def test_events_more_than_count(self):
        self._unittest_setup(EventsMoreThanCountHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(len(event_listeners),
                         PAGINATION_PAGE_COUNT + 1,
                         event_listeners)

    def test_events_equal_count(self):
        self._unittest_setup(EventsEqualToCountHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(len(event_listeners),
                         PAGINATION_PAGE_COUNT,
                         pprint.pformat(event_listeners))


class EmptyRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ''


class LinkTagRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<a href="/">click</a>'


class OnClickEventWithChildrenRequestHandler(ExtendedHttpRequestHandler):
    # https://stackoverflow.com/questions/1431812/prevent-javascript-onclick-on-child-element
    RESPONSE_BODY = ('''<div id="0" onclick="javascript:manualToggle(this)">
                            <span id="1">Allowed to click 1</span>
                            <span id="2">Allowed to click 2</span>
                        </div>
                        
                        <div>tag to force more complex selector</div>

                        <script>
                            function manualToggle(e) {
                              event.preventDefault();
                              
                              var elem = event.target;
                              
                              console.log(elem.attributes[0].value);
                            }
                        </script>
                        ''')


class OnClickEventChildrenNoInheritRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<table id="outside" onclick="modifyText();">
                            <tr><td id="t1">one</td></tr>
                        </table>

                        <script>
                            function modifyText(e) {
                              event.preventDefault();
                            }
                        </script>
                        ''')


class OnClickEventInvisibleTableRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<table id="outside" onclick="modifyText();">
                        </table>

                        <script>
                            function modifyText(e) {
                              event.preventDefault();
                            }
                        </script>
                        ''')


class TwoOnClickRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<div id="double" onclick="def();" onclick="abc();">
                            x
                        </div>

                        <script>
                            function abc(e) {
                              event.preventDefault();
                            }
                        </script>
                        <script>
                            function def(e) {
                              event.preventDefault();
                            }
                        </script>
                        ''')


class EventsEqualToCountHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<div onclick="def();">x</div>' * PAGINATION_PAGE_COUNT


class EventsLessThanCountHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<div onclick="def();">x</div>' * (PAGINATION_PAGE_COUNT - 1)


class EventsMoreThanCountHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<div onclick="def();">x</div>' * (PAGINATION_PAGE_COUNT + 1)
