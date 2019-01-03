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

    def test_onclick_event_listener_invisible_table(self):
        self._unittest_setup(OnClickEventInvisibleTableRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(event_listeners, [])

    def test_onclick_event_listener_children_that_do_not_inherit(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        self.assertEqual(event_listeners, [{u'tag_name': u'table',
                                            u'handler': u'modifyText();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'#outside'}])

    def test_html_events_filter_out_click(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(event_filter=['foobar'])

        self.assertEqual(event_listeners, [])

    def test_html_events_filter_in_click(self):
        self._unittest_setup(OnClickEventChildrenNoInheritRequestHandler)

        event_listeners = self.ic.get_html_event_listeners(event_filter=['click'])
        self._print_all_console_messages()
        self.assertEqual(event_listeners, [{u'tag_name': u'table',
                                            u'handler': u'modifyText();',
                                            u'event_type': u'click',
                                            u'node_type': 1,
                                            u'selector': u'#outside'}])

    def test_onclick_event_listener_with_children(self):
        self._unittest_setup(OnClickEventWithChildrenRequestHandler)

        event_listeners = self.ic.get_html_event_listeners()

        expected = [{u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'body > :nth-child(1)',
                     u'tag_name': u'div'},
                    {u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'body > :nth-child(1) > :nth-child(1)',
                     u'tag_name': u'span'},
                    {u'event_type': u'click',
                     u'node_type': 1,
                     u'handler': u'javascript:manualToggle(this)',
                     u'selector': u'body > :nth-child(1) > :nth-child(2)',
                     u'tag_name': u'span'}]

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
                                            u'selector': u'#double'}])


class EmptyRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ''


class LinkTagRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<a href="/">click</a>'


class OnClickEventWithChildrenRequestHandler(ExtendedHttpRequestHandler):
    # https://stackoverflow.com/questions/1431812/prevent-javascript-onclick-on-child-element
    RESPONSE_BODY = ('''<div id="0" onclick="javascript:manualToggle(this)">
                            <span id="1">Allowed to click</span>
                            <span id="2">Allowed to click</span>
                        </div>
                        
                        <div>tag to force more complex selector</>

                        <script>
                            function manualToggle(e) {
                              e.preventDefault();
                              
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
                              e.preventDefault();
                            }
                        </script>
                        ''')


class OnClickEventInvisibleTableRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Add_a_simple_listener
    RESPONSE_BODY = ('''<table id="outside" onclick="modifyText();">
                        </table>

                        <script>
                            function modifyText(e) {
                              e.preventDefault();
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
                              e.preventDefault();
                            }
                        </script>
                        <script>
                            function def(e) {
                              e.preventDefault();
                            }
                        </script>
                        ''')
