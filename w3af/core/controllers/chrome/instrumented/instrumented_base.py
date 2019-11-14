"""
instrumented_base.py

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

from requests import ConnectionError

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.tests.running_tests import is_running_tests
from w3af.core.controllers.profiling.utils.ps_mem import get_memory_usage
from w3af.core.controllers.chrome.devtools import DebugChromeInterface
from w3af.core.controllers.chrome.process import ChromeProcess
from w3af.core.controllers.chrome.proxy.main import LoggingProxy
from w3af.core.controllers.chrome.instrumented.utils import AllLoggingDisabled
from w3af.core.controllers.chrome.instrumented.exceptions import InstrumentedChromeException
from w3af.core.data.fuzzer.utils import rand_alnum


class InstrumentedChromeBase(object):
    """
    This class implements all the "boring" parts of the chrome instrumentation:

        1. Start a proxy server
        2. Start a chrome process that navigates via the proxy
        3. Close the browser

    The methods and features which communicate with Chrome to perform "interesting"
    actions are implemented in InstrumentedChrome
    """

    PROXY_HOST = '127.0.0.1'
    CHROME_HOST = '127.0.0.1'

    JS_ONERROR_HANDLER = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/onerror.js')
    JS_DOM_ANALYZER = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/dom_analyzer.js')
    JS_SELECTOR_GENERATOR = os.path.join(ROOT_PATH, 'core/controllers/chrome/js/optimal-select.min.js')

    def __init__(self, uri_opener, http_traffic_queue):
        self.uri_opener = uri_opener
        self.http_traffic_queue = http_traffic_queue

        self.id = rand_alnum(8)
        self.debugging_id = None

        self.proxy = self.start_proxy()
        self.chrome_process = self.start_chrome_process()
        self.chrome_conn = self.connect_to_chrome()

    def set_traffic_queue(self, http_traffic_queue):
        self.http_traffic_queue = http_traffic_queue
        self.proxy.set_traffic_queue(http_traffic_queue)

    def get_traffic_queue(self):
        return self.http_traffic_queue

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

        if not chrome_process.wait_for_start():
            stdout = '\n'.join(chrome_process.stdout)
            stderr = '\n'.join(chrome_process.stderr)
            args = (chrome_process.START_TIMEOUT_SEC, stdout, stderr)

            msg = ('Chrome process failed to start in %s seconds. The process'
                   ' stdout and stderr are:\n'
                   '\n'
                   '%s\n'
                   '\n'
                   '%s')

            raise InstrumentedChromeException(msg % args)

        return chrome_process

    def connect_to_chrome(self):
        port = self.chrome_process.get_devtools_port()
        chrome_id = self.chrome_process.get_id()

        # The timeout we specify here is the websocket timeout, which is used
        # for send() and recv() calls.
        try:
            chrome_conn = DebugChromeInterface(host=self.CHROME_HOST,
                                               port=port,
                                               timeout=0.001,
                                               debugging_id=self.debugging_id,
                                               chrome_id=chrome_id)
        except ConnectionError:
            msg = 'Failed to connect to Chrome on port %s'
            raise InstrumentedChromeException(msg % port)

        chrome_conn.name = 'DebugChromeInterface'
        chrome_conn.start()

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

    def terminate(self):
        om.out.debug('Terminating %s (did: %s)' % (self, self.debugging_id))

        if self.proxy is not None:
            try:
                self.proxy.stop()
            except Exception, e:
                msg = 'Failed to stop proxy server, exception: "%s" (did: %s)'
                args = (e, self.debugging_id)
                om.out.debug(msg % args)

        if self.chrome_conn is not None:
            try:
                # Close the browser in a clean way
                self.chrome_conn.Browser.close(ignore_result=True)
            except Exception as e:
                msg = 'Failed call Browser.close(), exception: "%s" (did: %s)'
                args = (e, self.debugging_id)
                om.out.debug(msg % args)

            try:
                with AllLoggingDisabled():
                    self.chrome_conn.close()
            except Exception as e:
                msg = 'Failed to close chrome connection, exception: "%s" (did: %s)'
                args = (e, self.debugging_id)
                om.out.debug(msg % args)

        if self.chrome_process is not None:
            try:
                # Kill the PID (if the process still exists after Browser.close())
                self.chrome_process.terminate()
            except Exception, e:
                msg = 'Failed to terminate chrome process, exception: "%s" (did: %s)'
                args = (e, self.debugging_id)
                om.out.debug(msg % args)

        self.proxy = None
        self.chrome_process = None
        self.chrome_conn = None

    def get_pid(self):
        try:
            return self.chrome_process.get_parent_pid()
        except:
            return None

    def get_memory_usage(self):
        """
        :return: The memory usage for the chrome process (parent) and all its
                 children (chrome uses various processes for rendering HTML)
        """
        parent = self.get_pid()

        if parent is None:
            return None, None

        children = self.chrome_process.get_children_pids()

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
