"""
test_crawler.py

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
import time
import unittest

import w3af.core.data.kb.config as cf

from w3af.core.controllers.output_manager import manager
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.db.variant_db import PATH_MAX_VARIANTS
from w3af.core.data.parsers.doc.url import URL
from w3af.plugins.crawl.web_spider import web_spider


class TestChromeCrawler(BaseChromeCrawlerTest):

    def test_crawl_one_url(self):
        self._unittest_setup(ExtendedHttpRequestHandler)

        self.crawler.crawl(self.fuzzable_request,
                           self.http_response,
                           self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        # One HTTP request, one for each RW strategy implemented in the
        # Chrome crawler class.
        request_1, response_1, debugging_id_1 = self.http_traffic_queue.get()

        self.assertEqual(request_1.get_url(), self.url)

    def test_crawl_xmlhttprequest(self):
        self._unittest_setup(XmlHttpRequestHandler)

        self.crawler.crawl(self.fuzzable_request,
                           self.http_response,
                           self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        request_1, response_1, debugging_id_1 = self.http_traffic_queue.get()
        request_2, response_2, debugging_id_2 = self.http_traffic_queue.get()

        # The first request is to load the main page
        self.assertEqual(request_1.get_url(), self.url)

        # The second request is the one sent using XMLHttpRequest
        # This request is sent on page load, without any interaction
        server_url = self.url.url_join('/server')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request_2.get_method(), 'POST')
        self.assertEqual(request_2.get_uri(), server_url)
        self.assertEqual(request_2.get_data(), data)


class TestChromeCrawlerWithWebSpider(unittest.TestCase):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()

        self.pool = Pool(processes=2,
                         worker_names='WorkerThread',
                         max_queued_tasks=20,
                         maxtasksperchild=20)

        self.web_spider = web_spider()
        self.web_spider.set_url_opener(self.uri_opener)
        self.web_spider.set_worker_pool(self.pool)

        fp_404_db = fingerprint_404_singleton(cleanup=True)
        fp_404_db.set_url_opener(self.uri_opener)

    def tearDown(self):
        # Process all events from the http traffic queue
        self.web_spider.has_pending_work()
        self.web_spider.end()

        self.server.shutdown()
        self.server_thread.join()

        manager.terminate()

        self.pool.close()
        self.pool.terminate()
        self.pool.join()

    def test_parse_dom(self):
        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=CreateLinksWithJS)

        self.server_thread = t
        self.server = s
        self.server_port = p

        target_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        target_url = URL(target_url)
        cf.cf.save('targets', [target_url, ])

        fuzzable_request = FuzzableRequest(target_url)
        self.web_spider.crawl(fuzzable_request, '0xdeadbeef')

        # Let the task start in ChromeCrawler._worker_pool before asking if there
        # is pending work
        time.sleep(1)

        while self.web_spider.has_pending_work():
            time.sleep(0.5)

        # The crawler sends a few requests to the target URL
        self.assertGreaterEqual(self.web_spider._chrome_identified_http_requests, 1)

        # But the links to the dynamically generated <a> tags should be in
        # the web_spider output queue
        expected_urls = set()
        for i in xrange(1000):
            expected_urls.add(target_url.url_join('/js-%s' % i))

        captured_urls = set()
        while self.web_spider.output_queue.qsize():
            captured_urls.add(self.web_spider.output_queue.get().get_url())

        intersect = expected_urls.intersection(captured_urls)
        self.assertEqual(len(intersect), PATH_MAX_VARIANTS)


class XmlHttpRequestHandler(ExtendedHttpRequestHandler):

    RESPONSE_BODY = '''<html>
                       <script>
                           var xhr = new XMLHttpRequest();
                           xhr.open("POST", '/server', true);
                        
                           //Send the proper header information along with the request
                           xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                        
                           xhr.onreadystatechange = function() {//Call a function when the state changes.
                               if(this.readyState == XMLHttpRequest.DONE && this.status == 200) {
                                   // Request finished. Do processing here.
                               }
                           }
                           xhr.send("foo=bar&lorem=ipsum"); 
                       </script>
                       </html>'''


class CreateLinksWithJS(ExtendedHttpRequestHandler):

    INDEX_BODY = '''
        <html>
            <body>
            <script>

                var i;

                for (i = 0; i < 1000; i++) { 
                    var a = document.createElement('a');
                    var linkText = document.createTextNode("my title text");
                    a.appendChild(linkText);
                    a.title = "my title text" + i;
                    a.href = "/js-" + i;
                    document.body.appendChild(a);
                }

            </script>
            </body>
        </html>
    '''

    JS_BODY = 'Magic!'

    NOT_FOUND_BODY = '404'

    def get_code_body(self, request_path):
        if 'js-' in request_path:
            return 200, self.JS_BODY

        if request_path.endswith('/'):
            return 200, self.INDEX_BODY

        return 404, self.NOT_FOUND_BODY
