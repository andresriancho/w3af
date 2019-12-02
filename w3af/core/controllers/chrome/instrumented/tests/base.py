"""
base.py

Copyright 2019 Andres Riancho

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
from __future__ import print_function

import Queue
import unittest

from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceException
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.tests.helpers import set_debugging_in_output_manager
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class BaseEventListenerCountTest(unittest.TestCase):

    def setUp(self):
        set_debugging_in_output_manager()

        uri_opener = ExtendedUrllib()
        http_traffic_queue = Queue.Queue()

        self.ic = InstrumentedChrome(uri_opener, http_traffic_queue)

    def tearDown(self):
        self.assertEqual(self.ic.get_js_errors(), [])
        self.ic.terminate()

    def _load_url(self, url):
        self.ic.load_url(url)

        loaded = self.ic.wait_for_load()
        
        if not loaded:
            self.ic.stop()

    def _print_all_console_messages(self):
        for console_message in self.ic.get_console_messages():
            print(console_message)

    def _print_summary(self, url, all_event_listeners):
        event_types = dict()

        for el in all_event_listeners:
            event_type = el['event_type']
            if event_type in event_types:
                event_types[event_type] += 1
            else:
                event_types[event_type] = 1

        # print(url)
        # pprint.pprint(event_types)
        # print()

    def _get_event_listeners(self, url):
        self._load_url(url)

        try:
            all_event_listeners = [el for el in self.ic.get_all_event_listeners()]
        except ChromeInterfaceException:
            all_event_listeners = []

        return all_event_listeners
