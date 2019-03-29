"""
test_instrumented_event_listeners.py

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


class TestChromeCrawlerGetEventListeners(unittest.TestCase):

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

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

    def test_no_event_handlers_link(self):
        self._unittest_setup(LinkTagRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

    def test_window_settimeout(self):
        self._unittest_setup(WindowSetTimeoutRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [{u'function': {}, u'timeout': 3000}])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

    def test_settimeout(self):
        self._unittest_setup(SetTimeoutRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [{u'function': {}, u'timeout': 3000}])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

    def test_setinterval(self):
        self._unittest_setup(WindowSetIntervalRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [{u'function': {}, u'timeout': 3000}])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

    def test_onclick_event_listener(self):
        self._unittest_setup(OnClickEventRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'tag_name': u'table',
                                                             u'node_type': 1,
                                                             u'selector': u'#outside',
                                                             u'event_type': u'click',
                                                             u'use_capture': False}])

    def test_onclick_event_listener_iter(self):
        self._unittest_setup(OnClickEventRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])

        result = []
        expected = [{u'tag_name': u'table',
                     u'node_type': 1,
                     u'selector': u'#outside',
                     u'event_type': u'click',
                     u'use_capture': False}]
        _iter = self.ic.get_js_event_listeners_iter()

        for i in _iter:
            result.append(i)

        self.assertEqual(result, expected)

    def test_onclick_anonymous_event_listener(self):
        self._unittest_setup(OnClickEventAnonymousRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'tag_name': u'table',
                                                             u'node_type': 1,
                                                             u'selector': u'#outside',
                                                             u'event_type': u'click',
                                                             u'use_capture': False}])

    def test_onclick_arrow_event_listener(self):
        self._unittest_setup(OnClickEventArrowRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'tag_name': u'table',
                                                             u'node_type': 1,
                                                             u'selector': u'#outside',
                                                             u'event_type': u'click',
                                                             u'use_capture': False}])

    def test_click_on_document(self):
        self._unittest_setup(EventListenerInDocument)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'event_type': u'click',
                                                             u'tag_name': u'!document',
                                                             u'node_type': 9,
                                                             u'selector': u'!document'}])

    def test_click_on_window(self):
        self._unittest_setup(EventListenerInWindow)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [{u'event_type': u'click',
                                                             u'tag_name': u'!window',
                                                             u'node_type': -1,
                                                             u'selector': u'!window'}])


class EmptyRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ''


class LinkTagRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<a href="/">click</a>'


class WindowSetTimeoutRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ('<script>'
                     '    window.setTimeout(function(){ console.log("Hello"); }, 3000);'
                     '</script>')


class SetTimeoutRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ('<script>'
                     '    setTimeout(function(){ console.log("Hello"); }, 3000);'
                     '</script>')


class WindowSetIntervalRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ('<script>'
                     '    window.setInterval(function(){ console.log("Hello"); }, 3000);'
                     '</script>')


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


class OnClickEventAnonymousRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Event_listener_with_anonymous_function
    RESPONSE_BODY = ('''<table id="outside">
                            <tr><td id="t1">one</td></tr>
                            <tr><td id="t2">two</td></tr>
                        </table>

                        <script>
                            // Function to change the content of t2
                            function modifyText(new_text) {
                              var t2 = document.getElementById("t2");
                              t2.firstChild.nodeValue = new_text;    
                            }
                             
                            // Function to add event listener to table
                            var el = document.getElementById("outside");
                            el.addEventListener("click", function(){modifyText("four")}, false);
                        </script>
                        ''')


class OnClickEventArrowRequestHandler(ExtendedHttpRequestHandler):
    # https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#Event_listener_with_an_arrow_function
    RESPONSE_BODY = ('''<table id="outside">
                            <tr><td id="t1">one</td></tr>
                            <tr><td id="t2">two</td></tr>
                        </table>

                        <script>
                            // Function to change the content of t2
                            function modifyText(new_text) {
                              var t2 = document.getElementById("t2");
                              t2.firstChild.nodeValue = new_text;    
                            }
                             
                            // Add event listener to table with an arrow function
                            var el = document.getElementById("outside");
                            el.addEventListener("click", () => { modifyText("four"); }, false);
                        </script>
                        ''')


class EventListenerInDocument(ExtendedHttpRequestHandler):
    # https://www.w3schools.com/jsref/tryit.asp?filename=tryjsref_document_addeventlistener
    RESPONSE_BODY = ('''<!DOCTYPE html>
                        <html>
                        <body>
                        
                        <p>This example uses the addEventListener() method to attach a click event to the document.</p>
                        
                        <p>Click anywhere in the document.</p>
                        
                        <p><strong>Note:</strong> The addEventListener() method is not supported in Internet Explorer 8 
                        and earlier versions.</p>
                        
                        <p id="demo"></p>
                        
                        <script>
                        document.addEventListener("click", function(){
                          document.getElementById("demo").innerHTML = "Hello World!" + (1+1);
                        });
                        </script>
                        
                        </body>
                        </html>
                        ''')


class EventListenerInWindow(ExtendedHttpRequestHandler):
    # https://www.w3schools.com/jsref/tryit.asp?filename=tryjsref_document_addeventlistener
    RESPONSE_BODY = ('''<!DOCTYPE html>
                        <html>
                        <body>

                        <p>This example uses the addEventListener() method to attach a click event to the document.</p>

                        <p>Click anywhere in the document.</p>

                        <p><strong>Note:</strong> The addEventListener() method is not supported in Internet Explorer 8 
                        and earlier versions.</p>

                        <p id="demo"></p>

                        <script>
                        window.addEventListener("click", function(){
                          document.getElementById("demo").innerHTML = "Hello World!" + (1+1);
                        });
                        </script>

                        </body>
                        </html>
                        ''')
