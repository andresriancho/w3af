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


class TestStateAcrossPages(BaseChromeCrawlerTest):

    def test_crawl_pages_with_same_footer(self):
        self._unittest_setup(MultiplePagesWithSameFooter)

        base_url_fmt = 'http://%s:%s/page-%%s' % (self.SERVER_HOST, self.server_port)
        log_url = 'http://%s:%s/log' % (self.SERVER_HOST, self.server_port)

        #
        # When we crawl the first page the crawler's state is empty, thus it will
        # find the onclick in div and dispatch it:
        #
        url = base_url_fmt % 1
        self.crawler.crawl(url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # /page-1 is loaded
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, url)

        # /log request is sent in learnMoreAboutUs()
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, log_url)

        #
        # When we crawl the exact same page again, the crawler state already contains
        # an entry for the div.onclick, so it will not run it again
        #
        url = base_url_fmt % 1
        self.crawler.crawl(url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        # /page-1 is loaded
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, url)

        #
        # But if will run the same div.onclick if it is found in a different URL
        # (notice the % 2 used right below to generate the different URL)
        #
        url = base_url_fmt % 2
        self.crawler.crawl(url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # /page-1 is loaded
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, url)

        # /log request is sent in learnMoreAboutUs()
        request, _ = self.http_traffic_queue.get()
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
            url = base_url_fmt % page_index
            self.crawler.crawl(url, self.http_traffic_queue)

            if self.http_traffic_queue.qsize() == 1:
                success = True
                break

            # /page-1 is loaded
            request, _ = self.http_traffic_queue.get()
            self.assertEqual(request.get_url().url_string, url)

            # /log request is sent in learnMoreAboutUs()
            request, _ = self.http_traffic_queue.get()
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
