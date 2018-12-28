"""
instrumented.py

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
import os
import re
import logging

from contextlib import contextmanager
from requests import ConnectionError

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.tests.running_tests import is_running_tests
from w3af.core.controllers.profiling.utils.ps_mem import get_memory_usage
from w3af.core.controllers.chrome.devtools import DebugChromeInterface
from w3af.core.controllers.chrome.process import ChromeProcess
from w3af.core.controllers.chrome.proxy import LoggingProxy
from w3af.core.data.fuzzer.utils import rand_alnum


class InstrumentedChrome(object):
    """
    1. Start a proxy server
    2. Start a chrome process that navigates via the proxy
    3. Load a page in Chrome (via the proxy)
    4. Receive Chrome events which indicate when the page load finished
    5. Close the browser

    More features to be implemented later.
    """

    PROXY_HOST = '127.0.0.1'
    CHROME_HOST = '127.0.0.1'
    PAGE_LOAD_TIMEOUT = 20
    PAGE_WILL_CHANGE_TIMEOUT = 1

    JS_ONERROR_HANDLER = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/onerror.js')
    JS_DOM_ANALYZER = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/dom_analyzer.js')
    JS_SELECTOR_GENERATOR = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/css-selector-generator.js')

    EVENT_TYPE_RE = re.compile('[a-zA-Z.]+')

    def __init__(self, uri_opener, http_traffic_queue):
        self.uri_opener = uri_opener
        self.http_traffic_queue = http_traffic_queue

        self.id = rand_alnum(8)
        self.debugging_id = None

        self.proxy = self.start_proxy()
        self.chrome_process = self.start_chrome_process()
        self.chrome_conn = self.connect_to_chrome()
        self.set_chrome_settings()

    def start_proxy(self):
        proxy = LoggingProxy(self.PROXY_HOST,
                             0,
                             self.uri_opener,
                             name='ChromeProxy',
                             queue=self.http_traffic_queue)

        proxy.set_debugging_id(self.debugging_id)

        proxy.start()
        proxy.wait_for_start()

        return proxy

    def get_proxy_address(self):
        return self.PROXY_HOST, self.proxy.get_bind_port()

    def get_first_response(self):
        return self.proxy.get_first_response()

    def get_first_request(self):
        return self.proxy.get_first_request()

    def start_chrome_process(self):
        chrome_process = ChromeProcess()

        proxy_host, proxy_port = self.get_proxy_address()
        chrome_process.set_proxy(proxy_host, proxy_port)

        chrome_process.start()
        chrome_process.wait_for_start()

        return chrome_process

    def connect_to_chrome(self):
        port = self.chrome_process.get_devtools_port()

        # The timeout we specify here is the websocket timeout, which is used
        # for send() and recv() calls. When we send a command wait_result() is
        # called, the websocket timeout might be exceeded multiple times while
        # waiting for the result.
        try:
            chrome_conn = DebugChromeInterface(host=self.CHROME_HOST,
                                               port=port,
                                               timeout=1,
                                               debugging_id=self.debugging_id)
        except ConnectionError:
            msg = 'Failed to connect to Chrome on port %s'
            raise InstrumentedChromeException(msg % port)

        return chrome_conn

    def set_dialog_handler(self, dialog_handler):
        self.chrome_conn.set_dialog_handler(dialog_handler)

    def dialog_handler(self, _type, message):
        """
        This is the default dialog handler, it will just print to the log file
        the contents of the alert / prompt message and continue.

        It is possible to override the default handler by calling
        set_dialog_handler() right after creating an InstrumentedChrome instance
        and before loading any page.

        Handles Page.javascriptDialogOpening event [0] which freezes the browser
        until it is dismissed.

        [0] https://chromedevtools.github.io/devtools-protocol/tot/Page#event-javascriptDialogOpening

        :param _type: One of alert, prompt, etc.
        :param message: The message shown in the aler / prompt
        :return: A tuple containing:
                    * True if we want to dismiss the alert / prompt or False if we
                      want to cancel it.

                    * The message to enter in the prompt (if this is a prompt).
        """
        msg = 'Chrome handled an %s dialog generated by the page. The message was: "%s"'
        args = (_type, message)
        om.out.debug(msg % args)

        return True, 'Bye!'

    def set_debugging_id(self, debugging_id):
        self.debugging_id = debugging_id
        self.chrome_conn.set_debugging_id(debugging_id)
        self.proxy.set_debugging_id(debugging_id)

    def set_chrome_settings(self):
        """
        Set any configuration settings required for Chrome
        :return: None
        """
        # Disable certificate validation
        self.chrome_conn.Security.setIgnoreCertificateErrors(ignore=True)

        # Disable CSP
        self.chrome_conn.Page.setBypassCSP(enabled=False)

        # Disable downloads
        self.chrome_conn.Page.setDownloadBehavior(behavior='deny')

        # Add JavaScript to be evaluated on every frame load
        self.chrome_conn.Page.addScriptToEvaluateOnNewDocument(source=self.get_dom_analyzer_source())

        # Handle alert and prompts
        self.set_dialog_handler(self.dialog_handler)

        # Enable events
        self.chrome_conn.Page.enable()
        self.chrome_conn.Page.setLifecycleEventsEnabled(enabled=True)

        # Enable console log events
        # https://chromedevtools.github.io/devtools-protocol/tot/Runtime#event-consoleAPICalled
        self.chrome_conn.Runtime.enable()

    def get_dom_analyzer_source(self):
        """
        :return: The JS source code for the DOM analyzer. This is a helper script
                 that runs on the browser side and extracts information for us.

                 According to the `addScriptToEvaluateOnNewDocument` docs:

                    Evaluates given script in every frame upon creation
                    (before loading frame's scripts).

                So we'll be able to override the addEventListener to analyze all
                on* handlers.
        """
        source = []

        if is_running_tests():
            js_onerror_source = file(self.JS_ONERROR_HANDLER).read()
            source.append(js_onerror_source)

        js_selector_generator_source = file(self.JS_SELECTOR_GENERATOR).read()
        source.append(js_selector_generator_source)

        js_dom_analyzer_source = file(self.JS_DOM_ANALYZER).read()
        source.append(js_dom_analyzer_source)

        return '\n\n'.join(source)

    def load_url(self, url):
        """
        Load an URL into the browser, start listening for events.

        :param url: The URL to load
        :return: This method returns immediately, even if the browser is not
                 able to load the URL and an error was raised.
        """
        url = str(url)
        self.chrome_conn.Page.navigate(url=url,
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
        :return: True if Page.frameScheduledNavigation event is found
        """
        events_to_wait_for = [
            {'event': 'Page.frameScheduledNavigation',
             'name': None,
             'timeout': self.PAGE_WILL_CHANGE_TIMEOUT},
        ]

        for event in events_to_wait_for:
            matching_message, messages = self.chrome_conn.wait_event(**event)

            if matching_message is None:
                return False

            msg = 'Received %s from Chrome during navigation_started (did: %s)'
            args = (event['event'], self.debugging_id)
            om.out.debug(msg % args)

        return True

    def wait_for_load(self):
        """
        Knowing when a page has completed loading is difficult

        This method will wait for two events:
            * Page.frameStoppedLoading
            * Page.lifecycleEvent with name networkIdle

        If they are not received within PAGE_LOAD_TIMEOUT the method gives up
        and assumes that it is the best thing it can do.

        :return: True when the two events were received
                 False when one or none of the events were received
        """
        events_to_wait_for = [
            {'event': 'Page.frameStoppedLoading',
             'name': None,
             'timeout': self.PAGE_LOAD_TIMEOUT},

            {'event': 'Page.lifecycleEvent',
             'name': 'networkAlmostIdle',
             'timeout': self.PAGE_LOAD_TIMEOUT}
        ]

        for event in events_to_wait_for:
            matching_message, messages = self.chrome_conn.wait_event(**event)

            if matching_message is None:
                return False

            msg = 'Received %s from Chrome while waiting for page load (did: %s)'
            args = (event['event'], self.debugging_id)
            om.out.debug(msg % args)

        return True

    def stop(self):
        """
        Stop loading any page and close.

        :return:
        """
        self.chrome_conn.Page.stopLoading()

    def get_dom(self):
        result = self.chrome_conn.Runtime.evaluate(expression='document.body.outerHTML')

        # This is a rare case where the DOM is not present
        if result is None:
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

    def navigate_to_history_index(self, index):
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
        return self.get_js_variable_value('window._DOMAnalyzer.set_timeouts')

    def get_js_set_intervals(self):
        return self.get_js_variable_value('window._DOMAnalyzer.set_intervals')

    def get_js_event_listeners(self):
        return self.get_js_variable_value('window._DOMAnalyzer.event_listeners')

    def get_html_event_listeners(self):
        return self.get_js_variable_value('window._DOMAnalyzer.getElementsWithEventHandlers()')

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

    def dispatch_js_event(self, selector, event_type):
        """
        Dispatch a new event in the browser
        :param selector: CSS selector for the element where the event is dispatched
        :param event_type: click, hover, etc.
        :return: Exceptions are raised on timeout and unknown events.
                 True is returned on success
        """
        assert self._is_valid_event_type(event_type)
        selector = self._escape_js_string(selector)

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
        om.out.debug('Terminating %s (did: %s)' % (self, self.debugging_id))

        try:
            self.proxy.stop()
        except Exception, e:
            msg = 'Failed to stop proxy server, exception: "%s" (did: %s)'
            args = (e, self.debugging_id)
            om.out.debug(msg % args)

        try:
            with all_logging_disabled:
                self.chrome_conn.close()
        except Exception, e:
            msg = 'Failed to close chrome connection, exception: "%s" (did: %s)'
            args = (e, self.debugging_id)
            om.out.debug(msg % args)

        try:
            self.chrome_process.terminate()
        except Exception, e:
            msg = 'Failed to terminate chrome process, exception: "%s" (did: %s)'
            args = (e, self.debugging_id)
            om.out.debug(msg % args)

        self.proxy = None
        self.chrome_process = None
        self.chrome_conn = None

    def get_pid(self):
        return self.chrome_process.get_parent_pid() if self.chrome_process is not None else None

    def get_memory_usage(self):
        """
        :return: The memory usage for the chrome process (parent) and all its
                 children (chrome uses various processes for rendering HTML)
        """
        parent = self.chrome_process.get_parent_pid()
        children = self.chrome_process.get_children_pids()

        if parent is None:
            return None, None

        _all = [parent]
        _all.extend(children)

        private, shared, count, total = get_memory_usage(_all, True)

        private = sum(p[1] for p in private)
        private = int(private)

        shared = sum(s[1] for s in shared.items())
        shared = int(shared)

        return private, shared

    def __str__(self):
        proxy_port = None
        devtools_port = None

        if self.proxy is not None:
            proxy_port = self.get_proxy_address()[1]

        if self.chrome_process is not None:
            devtools_port = self.chrome_process.get_devtools_port()

        pid = self.get_pid()

        args = (self.id, proxy_port, pid, devtools_port)
        msg = '<InstrumentedChrome (id:%s, proxy:%s, process_id: %s, devtools:%s)>'
        return msg % args


class InstrumentedChromeException(Exception):
    pass


class EventTimeout(Exception):
    pass


class EventException(Exception):
    pass


@contextmanager
def all_logging_disabled(highest_level=logging.CRITICAL):
    """
    A context manager that will prevent any logging messages
    triggered during the body from being processed.

    :param highest_level: The maximum logging level in use.
                          This would only need to be changed if a custom level
                          greater than CRITICAL is defined.
    """
    # two kind-of hacks here:
    #    * can't get the highest logging level in effect => delegate to the user
    #    * can't get the current module-level override => use an undocumented
    #       (but non-private!) interface
    previous_level = logging.root.manager.disable

    logging.disable(highest_level)

    try:
        yield
    finally:
        logging.disable(previous_level)

