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

from w3af.core.controllers.chrome.chrome_process import ChromeProcess
from w3af.core.controllers.daemons.proxy import Proxy, ProxyHandler


class InstrumentedChrome(object):
    """
    1. Start a proxy server
    2. Start a chrome process that navigates via the proxy
    3. Load a page in Chrome (via the proxy)
    4. Receive Chrome events which indicate when the page load finished
    5. Close the browser

    More features to be implemented later.
    """
    def __init__(self):
        self.proxy = self.create_proxy()
        self.chrome = self.start_chrome_process()

    def create_proxy(self):
        raise NotImplementedError

    def start_chrome_process(self):
        raise NotImplementedError

    def load_url(self, url):
        """
        Load an URL into the browser, start listening for events.

        :param url: The URL to load
        :return: This method returns immediately, even if the browser is not
                 able to load the URL and an error was raised.
        """
        raise NotImplementedError

    def load_completed(self):
        """
        :return: True when the page finished loading
        """
        raise NotImplementedError

    def terminate(self):
        self.chrome.terminate()
