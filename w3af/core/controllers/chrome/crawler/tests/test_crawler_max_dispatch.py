"""
test_crawler_max_dispatch.py

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
from mock import patch, PropertyMock

from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest
from w3af.core.controllers.chrome.crawler.tests.test_crawler_js import MultipleXmlHttpRequestHandler
from w3af.core.data.parsers.doc.url import URL


class TestCrawlMaxDispatchEvents(BaseChromeCrawlerTest):

    def test_crawl_pages_with_multiple_events_one(self):
        self._unittest_setup(MultipleXmlHttpRequestHandler)

        pointer = 'w3af.core.controllers.chrome.crawler.strategies.js.ChromeCrawlerJS.MAX_EVENTS_TO_DISPATCH'

        with patch(pointer, new_callable=PropertyMock) as max_mock:
            max_mock.return_value = 1
            self.crawler.crawl(self.fuzzable_request,
                               self.http_response,
                               self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # The first request is to load the main page
        request, _, _ = self.http_traffic_queue.get_nowait()
        self.assertEqual(request.get_url(), self.url)

        # The second request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _, _ = self.http_traffic_queue.get_nowait()

        server_url = self.url.url_join('/server_0')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)

    def test_crawl_pages_with_multiple_events_two(self):
        self._unittest_setup(MultipleXmlHttpRequestHandler)

        pointer = 'w3af.core.controllers.chrome.crawler.strategies.js.ChromeCrawlerJS.MAX_EVENTS_TO_DISPATCH'

        with patch(pointer, new_callable=PropertyMock) as max_mock:
            max_mock.return_value = 2
            self.crawler.crawl(self.fuzzable_request,
                               self.http_response,
                               self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 3)

        # The first request is to load the main page
        request, _, _ = self.http_traffic_queue.get_nowait()
        self.assertEqual(request.get_url(), self.url)

        # The second request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _, _ = self.http_traffic_queue.get_nowait()

        server_url = self.url.url_join('/server_0')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)

        # The second request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _, _ = self.http_traffic_queue.get_nowait()

        server_url = self.url.url_join('/server_1')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)

