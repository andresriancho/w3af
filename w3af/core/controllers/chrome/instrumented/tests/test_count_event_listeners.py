"""
test_count_event_listeners.py

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

from collections import OrderedDict
from nose.plugins.attrib import attr

from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceException
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.data.url.extended_urllib import ExtendedUrllib


@attr('internet')
class TestChromeCrawlerGetEventListeners(unittest.TestCase):
    """
    This test is the result of a small research I made to understand how many
    event listeners are present on "common" pages.

    Note that this test depends on external sites which we don't control in any
    way. The test might start failing after a change in those sites.

    Note that the test is tagged as 'internet' (see @attr) to be able to disable
    if necessary.
    """

    TESTS = OrderedDict([
        ('https://google.com/', 20),
        ('https://www.google.com/search?q=w3af', 70),

        ('https://www.bing.com/', 80),
        ('https://www.bing.com/search?q=w3af', 150),

        ('https://facebook.com/', 50),
        ('https://www.facebook.com/local/lists/350492278720904/', 5),

        ('https://cnn.com/', 0),
        ('https://edition.cnn.com/2019/03/27/uk/theresa-may-is-throwing-the-kitchen-sink-at-brexit-intl-gbr/index.html', 0),

        ('https://www.bbc.com/', 0),
        ('https://www.bbc.com/news/uk-politics-47729773', 1),

        ('https://www.wikipedia.org/', 3),
        ('https://en.wikipedia.org/wiki/Cross-site_scripting', 1),

        ('http://w3af.org/', 2),
        ('http://w3af.org/take-a-tour', 4),

        ('https://github.com/', 0),
        ('https://github.com/andresriancho/w3af', 0),

        ('https://web.whatsapp.com/', 0),
    ])

    def _load_url(self, url):
        uri_opener = ExtendedUrllib()
        http_traffic_queue = Queue.Queue()

        ic = InstrumentedChrome(uri_opener, http_traffic_queue)
        ic.load_url(url)
        ic.wait_for_load()

        return ic

    def _cleanup(self, ic):
        self.assertEqual(ic.get_js_errors(), [])
        ic.terminate()

    def _print_all_console_messages(self, ic):
        for console_message in ic.get_console_messages():
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

    def _count_event_listeners(self, url, min_event_count):
        ic = self._load_url(url)

        try:
            all_event_listeners = [el for el in ic.get_all_event_listeners()]
        except ChromeInterfaceException:
            all_event_listeners = []

        self._print_summary(url, all_event_listeners)

        msg = '%s has %s event listeners and should have at least %s'
        args = (url, len(all_event_listeners), min_event_count)

        self.assertGreaterEqual(len(all_event_listeners),
                                min_event_count,
                                msg % args)

    def test_count_event_listeners(self):
        for url, min_event_count in self.TESTS.iteritems():
            self._count_event_listeners(url, min_event_count)
