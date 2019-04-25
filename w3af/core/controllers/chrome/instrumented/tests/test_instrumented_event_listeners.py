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
from w3af.core.controllers.chrome.instrumented.tests.base import BaseInstrumentedUnittest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler


class TestChromeCrawlerGetEventListeners(BaseInstrumentedUnittest):
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

    def test_onclick_assign_to_onclick_event_listener(self):
        self._unittest_setup(OnClickEventSetOnClickRequestHandler)

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])
        self.assertEqual(self.ic.get_js_event_listeners(), [])

        # This case is handled in test_onclick_event_set_attribute
        # so it is OK for the get_js_event_listeners() to return an empty
        # list

    def test_onclick_event_listener_filter_positive(self):
        self._unittest_setup(OnClickEventRequestHandler)

        expected_response = [{u'tag_name': u'table',
                              u'node_type': 1,
                              u'selector': u'#outside',
                              u'event_type': u'click',
                              u'use_capture': False}]

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])

        self.assertEqual(self.ic.get_js_event_listeners(event_filter=['click']),
                         expected_response)

        self.assertEqual(self.ic.get_js_event_listeners(tag_name_filter=['table']),
                         expected_response)

        self.assertEqual(self.ic.get_js_event_listeners(event_filter=['click'],
                                                        tag_name_filter=['table']),
                         expected_response)

    def test_onclick_event_listener_filter_negative(self):
        self._unittest_setup(OnClickEventRequestHandler)

        expected_response = []

        self.assertEqual(self.ic.get_js_set_timeouts(), [])
        self.assertEqual(self.ic.get_js_set_intervals(), [])

        self.assertEqual(self.ic.get_js_event_listeners(event_filter=['load']),
                         expected_response)

        self.assertEqual(self.ic.get_js_event_listeners(tag_name_filter=['a']),
                         expected_response)

        self.assertEqual(self.ic.get_js_event_listeners(event_filter=['load'],
                                                        tag_name_filter=['a']),
                         expected_response)

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


class OnClickEventSetOnClickRequestHandler(ExtendedHttpRequestHandler):
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
                            el.onclick = modifyText;
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
