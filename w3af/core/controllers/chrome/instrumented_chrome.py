"""
instrumented_chrome.py

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
from w3af.core.controllers.chrome.chrome_interface import DebugChromeInterface
from w3af.core.controllers.chrome.chrome_process import ChromeProcess
from w3af.core.controllers.chrome.proxy import LoggingProxy


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

    def __init__(self, uri_opener, http_traffic_queue):
        self.uri_opener = uri_opener
        self.http_traffic_queue = http_traffic_queue

        self.proxy = self.start_proxy()
        self.chrome_process = self.start_chrome_process()
        self.chrome_conn = self.connect_to_chrome()

    def start_proxy(self):
        proxy = LoggingProxy(self.PROXY_HOST,
                             0,
                             self.uri_opener,
                             name='ChromeProxy',
                             queue=self.http_traffic_queue)

        proxy.start()
        proxy.wait_for_start()

        return proxy

    def get_proxy_address(self):
        return self.PROXY_HOST, self.proxy.get_bind_port()

    def start_chrome_process(self):
        chrome_process = ChromeProcess()

        proxy_host, proxy_port = self.get_proxy_address()
        chrome_process.set_proxy(proxy_host, proxy_port)

        chrome_process.start()
        chrome_process.wait_for_start()

        return chrome_process

    def connect_to_chrome(self):
        port = self.chrome_process.get_devtools_port()
        chrome_conn = DebugChromeInterface(host=self.CHROME_HOST,
                                           port=port)
        return chrome_conn

    def load_url(self, url):
        """
        Load an URL into the browser, start listening for events.

        :param url: The URL to load
        :return: This method returns immediately, even if the browser is not
                 able to load the URL and an error was raised.
        """
        self.chrome_conn.Page.navigate(url=url)

    def wait_for_load(self):
        """
        :return: True when the page finished loading
        """
        self.chrome_conn.wait_event("Page.frameStoppedLoading",
                                    timeout=self.PAGE_LOAD_TIMEOUT)

    def get_dom(self):
        result = self.chrome_conn.Runtime.evaluate(expression='document.body.outerHTML')
        return result['result']['result']['value']

    def terminate(self):
        self.chrome_process.terminate()
