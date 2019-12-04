"""
test_crawler_multiple_pages.py

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
from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.crawler.strategies.js import ChromeCrawlerJS
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers


class TestStateAcrossPages(BaseChromeCrawlerTest):

    def _get_request_response(self, _id):
        base_url_fmt = 'http://%s:%s/page-%%s' % (self.SERVER_HOST, self.server_port)

        url = URL(base_url_fmt % _id)
        fuzzable_request = FuzzableRequest(url)

        headers = Headers([('content-type', 'text/html')])
        http_response = HTTPResponse(200, '', headers, url, url, _id=1)

        return fuzzable_request, http_response

    def test_crawl_pages_with_same_footer(self):
        self._unittest_setup(MultiplePagesWithSameFooter)

        log_url = 'http://%s:%s/log' % (self.SERVER_HOST, self.server_port)

        #
        # When we crawl the first page the crawler's state is empty, thus it will
        # find the onclick in div and dispatch it:
        #
        fuzzable_request_1, http_response_1 = self._get_request_response(1)
        self.crawler.crawl(fuzzable_request_1,
                           http_response_1,
                           self.http_traffic_queue)
        self.crawler.wait_for_pending_tasks()

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # /page-1 is loaded
        request, _, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url(), fuzzable_request_1.get_uri())

        # /log request is sent in learnMoreAboutUs()
        request, _, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, log_url)

        #
        # When we crawl the exact same page again, the crawler state already contains
        # the URL, _should_crawl_with_chrome() will return False
        #
        fuzzable_request_1, http_response_1 = self._get_request_response(1)
        self.crawler.crawl(fuzzable_request_1,
                           http_response_1,
                           self.http_traffic_queue)
        self.crawler.wait_for_pending_tasks()

        self.assertEqual(self.http_traffic_queue.qsize(), 0)

        #
        # But if will run the same div.onclick if it is found in a different URL
        # (notice the 2 used right below to generate the different URL)
        #
        fuzzable_request_2, http_response_2 = self._get_request_response(2)
        self.crawler.crawl(fuzzable_request_2,
                           http_response_2,
                           self.http_traffic_queue)
        self.crawler.wait_for_pending_tasks()

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # /page-1 is loaded
        request, _, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url(), fuzzable_request_2.get_uri())

        # /log request is sent in learnMoreAboutUs()
        request, _, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, log_url)

        #
        # And now the last test, after a few runs the same div.onclick will NOT
        # be run because we don't want to send to run the same handlers over
        # and over
        #
        # Note that I use ChromeCrawlerJS.MAX_SIMILAR_EVENT_DISPATCH but the loop
        # should end before that, because of the multiple tests that I already
        # sent before the for loop
        #
        success = False

        for i in xrange(ChromeCrawlerJS.MAX_SIMILAR_EVENT_DISPATCH):
            page_index = i + 100

            fuzzable_request_n, http_response_n = self._get_request_response(page_index)
            self.crawler.crawl(fuzzable_request_n,
                               http_response_n,
                               self.http_traffic_queue)
            self.crawler.wait_for_pending_tasks()

            if self.http_traffic_queue.qsize() == 1:
                success = True
                break

            # /page-1 is loaded
            request, _, _ = self.http_traffic_queue.get()
            self.assertEqual(request.get_url(), fuzzable_request_n.get_uri())

            # /log request is sent in learnMoreAboutUs()
            request, _, _ = self.http_traffic_queue.get()
            self.assertEqual(request.get_url().url_string, log_url)

        self.assertTrue(success)


class MultiplePagesWithSameFooter(ExtendedHttpRequestHandler):
    BODY_WITH_FOOTER = '''
        <html>
            <body>
                <script>
                       function learnMoreAboutUs() {
                           var xhr = new XMLHttpRequest();
                           xhr.open("POST", '/log', true);

                           //Send the proper header information along with the request
                           xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

                           xhr.onreadystatechange = function() {//Call a function when the state changes.
                               if(this.readyState == XMLHttpRequest.DONE && this.status == 200) {
                                   // Request finished. Do processing here.
                               }
                           }
                           xhr.send("location=" + document.location.href);
                       } 
                </script>
                
                <footer>
                    <div onclick="learnMoreAboutUs();">
                        Learn more
                    </div>
                </footer>
            </body>
        </html>
    '''

    NOT_FOUND_BODY = '404'

    def get_code_body(self, request_path):
        if 'page-' in request_path:
            return 200, self.BODY_WITH_FOOTER

        if 'log' in request_path:
            return 200, 'Accepted'

        return 404, self.NOT_FOUND_BODY
