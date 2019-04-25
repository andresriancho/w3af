"""
main.py

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
import re
import time

from w3af.core.controllers.chrome.instrumented.instrumented_base import InstrumentedChromeBase
from w3af.core.controllers.chrome.instrumented.event_listener import EventListener
from w3af.core.controllers.chrome.instrumented.paginate import paginate, PAGINATION_PAGE_COUNT
from w3af.core.controllers.chrome.instrumented.exceptions import EventTimeout, EventException


class InstrumentedChrome(InstrumentedChromeBase):
    """
    1. Start a proxy server
    2. Start a chrome process that navigates via the proxy
    3. Load a page in Chrome (via the proxy)
    4. Receive Chrome events which indicate when the page load finished
    5. Close the browser

    More features to be implemented later.
    """

    PAGE_STATE_NONE = 0
    PAGE_STATE_LOADING = 1
    PAGE_STATE_LOADED = 2

    PAGE_LOAD_TIMEOUT = 10
    PAGE_WILL_CHANGE_TIMEOUT = 1

    EVENT_TYPE_RE = re.compile('[a-zA-Z.]+')

    def __init__(self, uri_opener, http_traffic_queue):
        super(InstrumentedChrome, self).__init__(uri_opener, http_traffic_queue)

        # These keep the internal state of the page based on received events
        self._frame_stopped_loading_event = None
        self._frame_scheduled_navigation = None
        self._network_almost_idle_event = None
        self._execution_context_created = None
        self._page_state = self.PAGE_STATE_NONE

        # Set the handler that will maintain the page state
        self.chrome_conn.set_event_handler(self._page_state_handler)

    def _page_state_handler(self, message):
        """
        This handler defines the current page state:
            * Null: Nothing has been loaded yet
            * Loading: Chrome is loading the page
            * Done: Chrome has completed loading the page

        :param message: The message as received from chrome
        :return: None
        """
        self._navigation_started_handler(message)
        self._load_url_finished_handler(message)

    def _navigation_started_handler(self, message):
        """
        The handler identifies events which are related to a new page being
        loaded in the browser (Page.Navigate or clicking on an element).

        :param message: The message from chrome
        :return: None
        """
        method = message.get('method', None)

        navigator_started_methods = ('Page.frameScheduledNavigation',
                                     'Page.frameStartedLoading',
                                     'Page.frameNavigated')

        if method in navigator_started_methods:
            self._frame_scheduled_navigation = True

            self._frame_stopped_loading_event = False
            self._network_almost_idle_event = False
            self._execution_context_created = False

            self._page_state = self.PAGE_STATE_LOADING
            return

    def _load_url_finished_handler(self, message):
        """
        Knowing when a page has completed loading is difficult

        This handler will wait for these chrome events:
            * Page.frameStoppedLoading
            * Page.lifecycleEvent with name networkIdle

        And set the corresponding flags so that wait_for_load() can return.

        :param message: The message from chrome
        :return: True when the two events were received
                 False when one or none of the events were received
        """
        if 'method' not in message:
            return

        elif message['method'] == 'Page.frameStoppedLoading':
            self._frame_stopped_loading_event = True

        elif message['method'] == 'Page.lifecycleEvent':
            if 'params' not in message:
                return

            if 'name' not in message['params']:
                return

            if message['params']['name'] == 'networkAlmostIdle':
                self._network_almost_idle_event = True

        elif message['method'] == 'Runtime.executionContextCreated':
            self._execution_context_created = True

        received_all = all([self._network_almost_idle_event,
                            self._frame_stopped_loading_event,
                            self._execution_context_created])

        if received_all:
            self._page_state = self.PAGE_STATE_LOADED

    def load_url(self, url):
        """
        Load an URL into the browser, start listening for events.

        :param url: The URL to load
        :return: This method returns immediately, even if the browser is not
                 able to load the URL and an error was raised.
        """
        self.chrome_conn.Page.navigate(url=str(url),
                                       timeout=self.PAGE_LOAD_TIMEOUT)

    def load_about_blank(self):
        self.load_url('about:blank')

    def navigation_started(self, timeout=None):
        """
        When an event is dispatched to the browser it is impossible to know
        before-hand if the JS code will trigger a page navigation to a
        new URL.

        Use this method after dispatching an event to know if the browser
        will go to a different URL.

        The method will wait `timeout` seconds for the browser event. If the
        event does not appear in `timeout` seconds then False is returned.

        :param timeout: How many seconds to wait for the event
        :return: True if the page state is PAGE_STATE_LOADING
        """
        timeout = timeout or self.PAGE_WILL_CHANGE_TIMEOUT
        start = time.time()

        while True:
            if self._page_state == self.PAGE_STATE_LOADING:
                return True

            if time.time() - start > timeout:
                return False

            time.sleep(0.1)

    def wait_for_load(self, timeout=None):
        """
        Knowing when a page has completed loading is difficult

        This method works together with _page_state_handler() that
        reads all events and sets the corresponding page state

        If the state is not reached within PAGE_LOAD_TIMEOUT or `timeout`
        the method will exit returning False

        :param timeout: Seconds to wait for the page state
        :return: True when the page state has reached PAGE_STATE_LOADED
                 False when not
        """
        timeout = timeout or self.PAGE_LOAD_TIMEOUT
        start = time.time()

        while True:
            if self._page_state == self.PAGE_STATE_LOADED:
                return True

            if time.time() - start > timeout:
                return False

            time.sleep(0.1)

    def stop(self):
        """
        Stop loading any page and close.

        :return:
        """
        self._page_state = self.PAGE_STATE_LOADED
        self.chrome_conn.Page.stopLoading()

    def get_url(self):
        result = self.chrome_conn.Runtime.evaluate(expression='document.location.href')
        return result['result']['result']['value']

    def get_dom(self):
        result = self.chrome_conn.Runtime.evaluate(expression='document.documentElement.outerHTML')

        # This is a rare case where the DOM is not present
        if result is None:
            return None

        exception_details = result.get('result', {}).get('exceptionDetails', {})
        if exception_details:
            return None

        return result['result']['result']['value']

    def get_navigation_history(self):
        """
        :return: The browser's navigation history, which looks like:
            {
              "currentIndex": 2,
              "entries": [
                {
                  "id": 1,
                  "url": "about:blank",
                  "userTypedURL": "about:blank",
                  "title": "",
                  "transitionType": "typed"
                },
                {
                  "id": 3,
                  "url": "http://127.0.0.1:45571/",
                  "userTypedURL": "http://127.0.0.1:45571/",
                  "title": "",
                  "transitionType": "typed"
                },
                {
                  "id": 5,
                  "url": "http://127.0.0.1:45571/a",
                  "userTypedURL": "http://127.0.0.1:45571/a",
                  "title": "",
                  "transitionType": "link"
                }
              ]
            }
        """
        result = self.chrome_conn.Page.getNavigationHistory()
        return result['result']

    def get_navigation_history_index(self):
        navigation_history = self.get_navigation_history()
        entries = navigation_history['entries']
        index = navigation_history['currentIndex']
        return entries[index]['id']

    def navigate_back(self):
        navigation_history = self.get_navigation_history()
        entries = navigation_history['entries']
        current_index = navigation_history['currentIndex']

        previous_index = current_index - 1
        previous_index = max(previous_index, len(entries))

        entry = entries[previous_index]
        return entry['id']

    def navigate_to_history_index(self, index):
        """
        Navigate to an index in the browser history

        This method does NOT guarantee that the index will exist.

        :param index: An index from Page.getNavigationHistory(), note that when
                      we talk about index in the navigation history it is the
                      value of the `id` attribute inside an item in `entries`

        :return: None
        """
        self.chrome_conn.Page.navigateToHistoryEntry(entryId=index)

    def _js_runtime_evaluate(self, expression, timeout=5):
        """
        A wrapper around Runtime.evaluate that provides error handling and
        timeouts.

        :param expression: The expression to evaluate

        :param timeout: The time to wait until the expression is run (in seconds)

        :return: The result of evaluating the expression, None if exceptions
                 were raised in JS during the expression execution.
        """
        result = self.chrome_conn.Runtime.evaluate(expression=expression,
                                                   returnByValue=True,
                                                   generatePreview=True,
                                                   awaitPromise=True,
                                                   timeout=timeout * 1000)

        # This is a rare case where the DOM is not present
        if result is None:
            return None

        if 'result' not in result:
            return None

        if 'result' not in result['result']:
            return None

        if 'value' not in result['result']['result']:
            return None

        return result['result']['result']['value']

    def get_js_variable_value(self, variable_name):
        """
        Read the value of a JS variable and return it. The value will be
        deserialized into a Python object.

        :param variable_name: The variable name. See the unittest at
                              test_load_page_read_js_variable to understand
                              how to reference a variable, it might be counter-
                              intuitive.

        :return: The variable value as a python object
        """
        return self._js_runtime_evaluate(variable_name)

    def get_js_errors(self):
        """
        This method should only be used during unit-testing, since it depends
        on onerror.js being loaded in get_dom_analyzer_source()

        :return: A list with all errors that appeared during the execution of
                 the JS code in the Chrome browser
        """
        return self.get_js_variable_value('window.errors')

    def get_js_set_timeouts(self):
        return list(self.get_js_set_timeouts_iter())

    def get_js_set_timeouts_iter(self):
        """
        :return: An iterator that can be used to read all the set interval handlers
        """
        for event in paginate(self.get_js_set_timeouts_paginated):
            yield event

    def get_js_set_timeouts_paginated(self,
                                      start=0,
                                      count=PAGINATION_PAGE_COUNT):
        """
        :param start: The index where to start the current batch at. This is
                      used for pagination purposes. The initial value is zero.

        :param count: The number of events to return in the result. The default
                      value is low, it is preferred to keep this number low in
                      order to avoid large websocket messages flowing from
                      chrome to the python code.

        :return: The event listeners
        """
        start = int(start)
        count = int(count)

        cmd = 'window._DOMAnalyzer.getSetTimeouts(%i, %i)'
        args = (start, count)

        return self.get_js_variable_value(cmd % args)

    def get_js_set_intervals(self):
        return list(self.get_js_set_intervals_iter())

    def get_js_set_intervals_iter(self):
        """
        :return: An iterator that can be used to read all the set interval handlers
        """
        for event in paginate(self.get_js_set_intervals_paginated):
            yield event

    def get_js_set_intervals_paginated(self,
                                       start=0,
                                       count=PAGINATION_PAGE_COUNT):
        """
        :param start: The index where to start the current batch at. This is
                      used for pagination purposes. The initial value is zero.

        :param count: The number of events to return in the result. The default
                      value is low, it is preferred to keep this number low in
                      order to avoid large websocket messages flowing from
                      chrome to the python code.

        :return: The event listeners
        """
        start = int(start)
        count = int(count)

        cmd = 'window._DOMAnalyzer.getSetIntervals(%i, %i)'
        args = (start, count)

        return self.get_js_variable_value(cmd % args)

    def get_js_event_listeners(self,
                               event_filter=None,
                               tag_name_filter=None):
        """
        get_js_event_listeners_iter() should be used in most scenarios to prevent
        huge json blobs from being sent from the browser to w3af

        :return: A list of event listeners
        """
        return list(self.get_js_event_listeners_iter(event_filter=event_filter,
                                                     tag_name_filter=tag_name_filter))

    def get_js_event_listeners_iter(self,
                                    event_filter=None,
                                    tag_name_filter=None):
        """
        :return: An iterator that can be used to read all the event listeners
        """
        for event in paginate(self.get_js_event_listeners_paginated,
                              event_filter=event_filter,
                              tag_name_filter=tag_name_filter):
            yield event

    def get_js_event_listeners_paginated(self,
                                         start=0,
                                         count=PAGINATION_PAGE_COUNT,
                                         event_filter=None,
                                         tag_name_filter=None):
        """
        :param start: The index where to start the current batch at. This is
                      used for pagination purposes. The initial value is zero.

        :param count: The number of events to return in the result. The default
                      value is low, it is preferred to keep this number low in
                      order to avoid large websocket messages flowing from
                      chrome to the python code.

        :return: The event listeners
        """
        start = int(start)
        count = int(count)

        event_filter = event_filter or []
        event_filter = list(event_filter)
        event_filter = repr(event_filter)

        tag_name_filter = tag_name_filter or []
        tag_name_filter = list(tag_name_filter)
        tag_name_filter = repr(tag_name_filter)

        cmd = 'window._DOMAnalyzer.getEventListeners(%s, %s, %i, %i)'
        args = (event_filter, tag_name_filter, start, count)

        event_listeners = self.get_js_variable_value(cmd % args)

        if event_listeners is None:
            # Something happen here... potentially a bug in the instrumented
            # chrome or the dom_analyzer.js code
            return

        for event_listener in event_listeners:
            yield EventListener(event_listener)

    def get_html_event_listeners_iter(self,
                                      event_filter=None,
                                      tag_name_filter=None):
        """
        :param event_filter: A list containing the events to filter by.
                     For example if only the "click" events are
                     required, the value of event_filter should be
                     ['click']. Use an empty filter to return all DOM
                     events.

        :param tag_name_filter: A list containing the tag names to filter by.
                                For example if only the "div" tags should be
                                returned, the value of tag_name_filter should be
                                ['div']. Use an empty filter to return events for
                                all DOM tags.

        :return: The DOM events that match the filters
        """
        for event in paginate(self.get_html_event_listeners_paginated,
                              event_filter=event_filter,
                              tag_name_filter=tag_name_filter):
            yield event

    def get_html_event_listeners(self,
                                 event_filter=None,
                                 tag_name_filter=None):
        """
        :param event_filter: A list containing the events to filter by.
                     For example if only the "click" events are
                     required, the value of event_filter should be
                     ['click']. Use an empty filter to return all DOM
                     events.

        :param tag_name_filter: A list containing the tag names to filter by.
                                For example if only the "div" tags should be
                                returned, the value of tag_name_filter should be
                                ['div']. Use an empty filter to return events for
                                all DOM tags.

        :return: The DOM events that match the filters
        """
        return list(self.get_html_event_listeners_iter(event_filter=event_filter,
                                                       tag_name_filter=tag_name_filter))

    def get_html_event_listeners_paginated(self,
                                           start=0,
                                           count=PAGINATION_PAGE_COUNT,
                                           event_filter=None,
                                           tag_name_filter=None):
        """
        :param start: The index where to start the current batch at. This is
                      used for pagination purposes. The initial value is zero.

        :param count: The number of events to return in the result. The default
                      value is low, it is preferred to keep this number low in
                      order to avoid large websocket messages flowing from
                      chrome to the python code.

        :param event_filter: A list containing the events to filter by.
                             For example if only the "click" events are
                             required, the value of event_filter should be
                             ['click']. Use an empty filter to return all DOM
                             events.

        :param tag_name_filter: A list containing the tag names to filter by.
                                For example if only the "div" tags should be
                                returned, the value of tag_name_filter should be
                                ['div']. Use an empty filter to return events for
                                all DOM tags.

        :return: The DOM events that match the filters
        """
        start = int(start)
        count = int(count)

        event_filter = event_filter or []
        event_filter = list(event_filter)
        event_filter = repr(event_filter)

        tag_name_filter = tag_name_filter or []
        tag_name_filter = list(tag_name_filter)
        tag_name_filter = repr(tag_name_filter)

        cmd = 'window._DOMAnalyzer.getElementsWithEventHandlers(%s, %s, %i, %i)'
        args = (event_filter, tag_name_filter, start, count)

        event_listeners = self.get_js_variable_value(cmd % args)

        if event_listeners is None:
            # Something happen here... potentially a bug in the instrumented
            # chrome or the dom_analyzer.js code
            return

        for event_listener in event_listeners:
            yield EventListener(event_listener)

    def get_all_event_listeners(self,
                                event_filter=None,
                                tag_name_filter=None):

        for event_listener in self.get_js_event_listeners_iter(event_filter=event_filter,
                                                               tag_name_filter=tag_name_filter):
            yield event_listener

        for event_listener in self.get_html_event_listeners_iter(event_filter=event_filter,
                                                                 tag_name_filter=tag_name_filter):
            yield event_listener

    def _is_valid_event_type(self, event_type):
        """
        Validation function to make sure that a specially crafted page can not
        inject JS into dispatch_js_event() and other functions that generate code
        that is then eval'ed

        :param event_type: an event type (eg. click)
        :return: True if valid
        """
        return bool(self.EVENT_TYPE_RE.match(event_type))

    def _escape_js_string(self, text):
        """
        Escapes any double quotes that exist in text. Prevents specially crafted
        pages from injecting JS into functions like dispatch_js_event() that
        generate code that is then eval'ed.

        :param text: The javascript double quoted string to escape
        :return: The string with any double quotes escaped with \
        """
        return text.replace('"', '\\"')

    def capture_screenshot(self):
        """
        :return: The base64 encoded bytes of the captured image
        """
        response = self.chrome_conn.Page.captureScreenshot()

        return response['result']['data']

    def dispatch_js_event(self, selector, event_type):
        """
        Dispatch a new event in the browser
        :param selector: CSS selector for the element where the event is dispatched
        :param event_type: click, hover, etc.
        :return: Exceptions are raised on timeout and unknown events.
                 True is returned on success
        """
        # Perform input validation
        assert self._is_valid_event_type(event_type)
        selector = self._escape_js_string(selector)

        # Dispatch the event that will potentially trigger _navigation_started_handler()
        cmd = 'window._DOMAnalyzer.dispatchCustomEvent("%s", "%s")'
        args = (selector, event_type)

        result = self._js_runtime_evaluate(cmd % args)

        if result is None:
            raise EventTimeout('The event execution timed out')

        elif result is False:
            # This happens when the element associated with the event is not in
            # the DOM anymore
            raise EventException('The event was not run')

        return True

    def get_console_messages(self):
        console_message = self.chrome_conn.read_console_message()

        while console_message is not None:
            yield console_message
            console_message = self.chrome_conn.read_console_message()

    def terminate(self):
        super(InstrumentedChrome, self).terminate()
        self._page_state = self.PAGE_STATE_NONE
