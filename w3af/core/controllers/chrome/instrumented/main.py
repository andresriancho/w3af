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
import time
import json

import w3af.core.controllers.output_manager as om

from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.chrome.instrumented.instrumented_base import InstrumentedChromeBase
from w3af.core.controllers.chrome.instrumented.event_listener import EventListener
from w3af.core.controllers.chrome.login.login_form import LoginForm
from w3af.core.controllers.chrome.instrumented.page_state import PageState
from w3af.core.controllers.chrome.instrumented.paginate import paginate, PAGINATION_PAGE_COUNT
from w3af.core.controllers.chrome.instrumented.utils import escape_js_string, is_valid_event_type
from w3af.core.controllers.chrome.instrumented.frame_manager import FrameManager
from w3af.core.controllers.chrome.instrumented.exceptions import (EventTimeout,
                                                                  EventException,
                                                                  InstrumentedChromeException)


class InstrumentedChrome(InstrumentedChromeBase):
    """
    1. Start a proxy server
    2. Start a chrome process that navigates via the proxy
    3. Load a page in Chrome (via the proxy)
    4. Receive Chrome events which indicate when the page load finished
    5. Close the browser

    More features to be implemented later.
    """

    PAGE_LOAD_TIMEOUT = 10
    PAGE_WILL_CHANGE_TIMEOUT = 1

    def __init__(self, uri_opener, http_traffic_queue):
        super(InstrumentedChrome, self).__init__(uri_opener, http_traffic_queue)

        self.frame_manager = FrameManager(self.debugging_id)
        self.page_state = PageState(self.frame_manager,
                                    self.proxy,
                                    self.debugging_id)

        # Set the handler that will maintain the page and frame state
        self.chrome_conn.set_event_handler(self.frame_manager.frame_manager_handler)

        # Set the chrome settings after configuring the handlers, this is required
        # to receive some of the messages which are sent early on during the
        # initialization phase
        self.set_chrome_settings()

    def load_url(self, url):
        """
        Load an URL into the browser, start listening for events.

        :param url: The URL to load
        :return: This method returns immediately, even if the browser is not
                 able to load the URL and an error was raised.
        """
        self._force_page_loading_state()
        self.chrome_conn.Page.navigate(url=str(url),
                                       timeout=self.PAGE_LOAD_TIMEOUT,
                                       transitionType='link')

    def load_about_blank(self):
        self.clear_state()
        self.load_url('about:blank')

    def clear_state(self):
        self.frame_manager = FrameManager(self.debugging_id)
        self.page_state = PageState(self.frame_manager,
                                    self.proxy,
                                    self.debugging_id)

    def set_debugging_id(self, debugging_id):
        super(InstrumentedChrome, self).set_debugging_id(debugging_id)
        self.frame_manager.set_debugging_id(debugging_id)
        self.page_state.set_debugging_id(debugging_id)

    def get_debugging_id(self):
        return self.debugging_id

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
        :return: True if the page state is STATE_LOADING
        """
        timeout = timeout or self.PAGE_WILL_CHANGE_TIMEOUT
        start = time.time()

        while True:
            if time.time() - start > timeout:
                return False

            if self.page_state.get() == PageState.STATE_LOADING:
                return True

            time.sleep(0.1)

    def wait_for_load(self, timeout=None):
        """
        Knowing when a page has completed loading is difficult

        This method works together with _page_state_handler() that
        reads all events and sets the corresponding page state

        If the state is not reached within PAGE_LOAD_TIMEOUT or `timeout`
        the method will exit returning False

        :param timeout: Seconds to wait for the page state
        :return: True when the page state has reached STATE_LOADED
                 False when not
        """
        timeout = timeout or self.PAGE_LOAD_TIMEOUT
        start = time.time()

        main_frame = self.frame_manager.get_main_frame()
        main_frame_id = main_frame.frame_id if main_frame is not None else None

        while True:
            if time.time() - start > timeout:
                msg = 'wait_for_load(timeout=%s) timed out (did: %s, main_frame: %s)'
                args = (timeout, self.debugging_id, main_frame_id)
                om.out.debug(msg % args)

                return False

            if self.page_state.get() == PageState.STATE_LOADED:
                return True

            time.sleep(0.15)

    def stop(self):
        """
        Stop loading any page and close.

        :return:
        """
        self.page_state.force(PageState.STATE_LOADED)
        self.chrome_conn.Page.stopLoading()

    def get_url(self):
        """
        :return: The current URL for the chrome instance or None if there is
                 no page loaded
        """
        result = self.chrome_conn.Runtime.evaluate(expression='document.location.href')
        url_string = result['result']['result']['value']

        try:
            url = URL(url_string)
        except ValueError:
            #
            # This happens in some rare cases when the URL in the browser tab
            # is set to about:blank , which is an invalid URL for the w3af
            # framework
            #
            # Callers to this method need to handle None as a result
            #
            url = None

        return url

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
        if previous_index < 0:
            raise InstrumentedChromeException('Invalid history index')

        entry = entries[previous_index]
        self.navigate_to_history_index(entry['id'])

    def navigate_to_history_index(self, index):
        """
        Navigate to an index in the browser history

        This method does NOT guarantee that the index will exist.

        :param index: An index from Page.getNavigationHistory(), note that when
                      we talk about index in the navigation history it is the
                      value of the `id` attribute inside an item in `entries`

        :return: None
        """
        self._force_page_loading_state()
        self.chrome_conn.Page.navigateToHistoryEntry(entryId=index)

    def dispatch_js_event(self, selector, event_type):
        """
        Dispatch a new event in the browser
        :param selector: CSS selector for the element where the event is dispatched
        :param event_type: click, hover, etc.
        :return: Exceptions are raised on timeout and unknown events.
                 True is returned on success
        """
        # Perform input validation
        assert is_valid_event_type(event_type)
        selector = escape_js_string(selector)

        # Dispatch the event that will potentially trigger _navigation_started_handler()
        cmd = 'window._DOMAnalyzer.dispatchCustomEvent("%s", "%s")'
        args = (selector, event_type)

        self._force_might_navigate_state()
        result = self.js_runtime_evaluate(cmd % args)

        if result is None:
            raise EventTimeout('The event execution timed out')

        elif result is False:
            # This happens when the element associated with the event is not in
            # the DOM anymore
            raise EventException('The event was not run')

        return True

    def get_login_forms(self):
        """
        :return: Yield LoginForm instances
        """
        result = self.js_runtime_evaluate('window._DOMAnalyzer.getLoginForms()')

        if result is None:
            raise EventTimeout('The event execution timed out')

        for form in json.loads(result):
            login_form = LoginForm()

            login_form.set_password_css_selector(form['password'])
            login_form.set_username_css_selector(form['username'])
            login_form.set_parent_css_selector(form['parent'])
            login_form.set_submit_css_selector(form['submit'])

            yield login_form

    def get_login_forms_without_form_tags(self):
        """
        :return: Yield LoginForm instances
        """
        result = self.js_runtime_evaluate('window._DOMAnalyzer.getLoginFormsWithoutFormTags()')

        if result is None:
            raise EventTimeout('The event execution timed out')

        for form in json.loads(result):
            login_form = LoginForm()

            login_form.set_password_css_selector(form['password'])
            login_form.set_username_css_selector(form['username'])
            login_form.set_parent_css_selector(form['parent'])
            login_form.set_submit_css_selector(form['submit'])

            yield login_form

    def type_text(self, text, selector=None):
        """
        Types `text` on HTML input specified by `selector`.

        This method is generic enough to send any combination of keys to any
        tag in the DOM, but in 99% of the cases we're using it to type some
        text into a form <input>.

        Implementation is inspired by puppeteer [0].

        [0] https://github.com/puppeteer/puppeteer/blob/3773229ac276a84a4de113e74290abc3bbf60499/lib/Input.js#L158-L182

        :param text: The string to type
        :param selector: The CSS selector pointing to the HTML tag
        :return: True if the text was sent to the tag
        """
        if selector is not None:
            focused_on_selector = self.focus(selector)

            if not focused_on_selector:
                msg = 'Failed to focus on CSS selector "%s" (did: %s)'
                args = (selector, self.debugging_id)
                om.out.debug(msg % args)
                return False

        for key in text:
            if not self.key_down(key):
                return False

            if not self.key_up():
                return False

        return True

    def get_dom_document_node_id(self):
        result = self.chrome_conn.DOM.getDocument()

        # This is a rare case where the API call failed
        if result is None:
            return None

        node_id = result.get('result', {}).get('root', {}).get('nodeId', None)

        if node_id is None:
            return None

        return node_id

    def focus(self, selector):
        """
        Sets focus to the given selector, when using the browser with a UI this
        is achieved by clicking on the <input> or <textarea> tag.

        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelectorAll
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-focus

        :param selector: The CSS selector pointing to the HTML tag to focus on
        :return: True if chrome was able to focus on the selector
        """
        node_id = self.get_dom_document_node_id()

        if node_id is None:
            return False

        result = self.chrome_conn.DOM.querySelectorAll(nodeId=node_id,
                                                       selector=selector)

        # This is a rare case where the API call failed
        if result is None:
            return None

        node_ids = result.get('result', {}).get('nodeIds', None)

        if node_ids is None:
            msg = ('The call to chrome.focus() failed.'
                   ' CSS selector "%s" returned no nodes (did: %s)')
            args = (selector, self.debugging_id)
            om.out.debug(msg % args)
            return False

        if len(node_ids) > 1:
            msg = ('The call to chrome.focus() failed.'
                   ' CSS selector "%s" returned more than one node (did: %s)')
            args = (selector, self.debugging_id)
            om.out.debug(msg % args)
            return False

        node_id = node_ids[0]

        result = self.chrome_conn.DOM.focus(nodeId=node_id)

        # This is a rare case where the API call failed
        if result is None:
            return False

        return True

    def press_enter_key(self):
        """
        Press the enter key in Chrome. This method is commonly used together
        with the focus(), first focus on the element where you want to send
        the key and then send it.

        :return: None
        """
        result = self.chrome_conn.Input.dispatchKeyEvent(type='char',
                                                         key='Enter',
                                                         unmodifiedText='\r',
                                                         text='\r')

        if result is None:
            return False

        # Let the rest of the world know that the browser might navigate
        # away from the current page because of the enter key that we
        # just pressed
        self._force_might_navigate_state()

        result = self.chrome_conn.Input.dispatchKeyEvent(type='keyUp')

        if result is None:
            return False

        return True

    def press_tab_key(self):
        """
        Press the tab key in Chrome. This method is commonly used together
        with the focus(), first focus on the element where you want to send
        the key and then send it.

        :return: None
        """
        result = self.chrome_conn.Input.dispatchKeyEvent(type='rawKeyDown',
                                                         modifiers=0,
                                                         windowsVirtualKeyCode=9,
                                                         code='Tab',
                                                         key='Tab',
                                                         unmodifiedText='\t',
                                                         text='\t')

        if result is None:
            return False

        result = self.chrome_conn.Input.dispatchKeyEvent(type='keyUp')

        if result is None:
            return False

        return True

    def key_down(self, key):
        """
        Uses Input [0] to send key down event. Inspired on [1]

        [0] https://chromedevtools.github.io/devtools-protocol/tot/Input
        [1] https://github.com/puppeteer/puppeteer/blob/3773229ac276a84a4de113e74290abc3bbf60499/lib/Input.js#L43

        :return: None
        """
        result = self.chrome_conn.Input.dispatchKeyEvent(type='keyDown',
                                                         text=key)

        if result is None:
            return False

        return True

    def key_up(self):
        """
        Uses Input [0] to send key up event. Inspired on [1]

        [0] https://chromedevtools.github.io/devtools-protocol/tot/Input
        [1] https://github.com/puppeteer/puppeteer/blob/3773229ac276a84a4de113e74290abc3bbf60499/lib/Input.js#L132

        :return: None
        """
        result = self.chrome_conn.Input.dispatchKeyEvent(type='keyUp')

        if result is None:
            return False

        return True

    def _force_page_loading_state(self):
        """
        During testing it was possible to identify cases where the code was
        doing the right thing:

            ic.navigate_to_history_index(index_before)
            ic.wait_for_load()
            ic.get_dom()

        Starting navigation, waiting for the page to load, and then reading
        the DOM. The problem was that:

            * navigate_to_history_index started navigation and returned
              a result in the websocket

            * the messages indicating that the navigation had started
              did not arrive quickly enough, so the wait_for_load()
              method returned: the page was already loaded

            * page loading started and life cycle events arrived

            * (page loading is incomplete) and get_dom() is called

            * TypeError: Cannot read property 'outerHTML' of null
              was returned by Chrome, because the 'document' did not
              exist yet.

        The solution to this issue was to:

            * Force the page state to STATE_LOADING when we know that
              the action we're performing (eg. navigate_to_history_index)
              was going to trigger a load. This is performed in this method

            * Set the page state to MIGHT_NAVIGATE when the action
              we took (eg. dispatching an event) might or might not trigger a
              page load.

        :return: None
        """
        main_frame = self.frame_manager.get_main_frame()
        if main_frame is not None:
            main_frame.set_navigated()

        self.page_state.force(PageState.STATE_LOADING)

    def _force_might_navigate_state(self):
        """
        :see: Documentation at _force_page_loading_state().
        """
        self.page_state.force(PageState.MIGHT_NAVIGATE)

    def js_runtime_evaluate(self, expression, timeout=5):
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
                                                   timeout=timeout)

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
        return self.js_runtime_evaluate(variable_name)

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

        for event_listener in json.loads(event_listeners):
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

        for event_listener in json.loads(event_listeners):
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

    def get_screenshot(self):
        """
        :return: The base64 encoded bytes of the captured image
        """
        response = self.chrome_conn.Page.captureScreenshot()

        return response['result']['data']

    def get_console_messages(self):
        console_message = self.chrome_conn.read_console_message()

        while console_message is not None:
            yield console_message
            console_message = self.chrome_conn.read_console_message()

    def terminate(self):
        super(InstrumentedChrome, self).terminate()
        self.page_state.force(PageState.STATE_NONE)
        self.clear_state()
