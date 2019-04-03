"""
test_crawl_internet_pages.py

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
import pprint

from collections import OrderedDict
from nose.plugins.attrib import attr

from w3af.core.controllers.chrome.crawler.main import ChromeCrawler
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.controllers.chrome.tests.helpers import set_debugging_in_output_manager


@attr('internet')
class TestChromeCrawlerInternetPages(unittest.TestCase):
    """
    This test is the result of debugging and experimenting how the crawler will
    work on "common" pages.

    Note that this test depends on external sites which we don't control in any
    way. The test might start failing after a change in those sites.

    Note that the test is tagged as 'internet' (see @attr) to be able to disable
    if necessary.

    Feel free to skip this test if it doesn't work anymore.
    """

    TESTS = OrderedDict([
        #('https://www.google.com/', 100),
        ('https://www.google.com/search?q=w3af', 100),
    ])
    """
    ('https://www.bing.com/', 100),
    ('https://www.bing.com/search?q=w3af', 100),

    ('https://facebook.com/', 100),
    ('https://www.facebook.com/local/lists/350492278720904/', 100),

    ('https://cnn.com/', 100),
    ('https://edition.cnn.com/2019/03/27/uk/theresa-may-is-throwing-the-kitchen-sink-at-brexit-intl-gbr/index.html', 100),

    ('https://www.bbc.com/', 100),
    ('https://www.bbc.com/news/uk-politics-47729773', 100),

    ('https://www.wikipedia.org/', 100),
    ('https://en.wikipedia.org/wiki/Cross-site_scripting', 100),

    ('http://w3af.org/', 100),
    ('http://w3af.org/take-a-tour', 100),

    ('https://github.com/', 100),
    ('https://github.com/andresriancho/w3af', 100),

    ('https://web.whatsapp.com/', 100),
    """

    def _get_crawler(self):
        uri_opener = ExtendedUrllib()
        http_traffic_queue = Queue.Queue()

        crawler = ChromeCrawler(uri_opener)

        return crawler, http_traffic_queue

    def _cleanup(self, crawler):
        crawler.terminate()

    def _get_found_urls(self, http_traffic_queue):
        uris = set()

        while not http_traffic_queue.empty():
            request, response = http_traffic_queue.get_nowait()
            uris.add(request.get_uri())

        return uris

    def _crawl(self, url, min_event_count):
        crawler, http_traffic_queue = self._get_crawler()

        crawler.crawl(url, http_traffic_queue)

        found_uris = self._get_found_urls(http_traffic_queue)

        self.assertEqual(crawler.get_js_errors(), [])

        self.assertGreaterEqual(len(found_uris),
                                min_event_count,
                                pprint.pformat(found_uris))

    def test_count_event_listeners(self):
        set_debugging_in_output_manager()

        for url, min_found_urls in self.TESTS.iteritems():
            self._crawl(url, min_found_urls)
