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
import Queue
import unittest

from w3af.core.controllers.chrome.crawler import ChromeCrawler
from w3af.core.controllers.chrome.tests.test_instrumented import InstrumentedChromeHandler
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.parsers.doc.url import URL


class TestChromeCrawler(unittest.TestCase):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=InstrumentedChromeHandler)

        self.server_thread = t
        self.server = s
        self.server_port = p

        self.crawler = ChromeCrawler(self.uri_opener)

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        self.crawler.terminate()
        self.server.shutdown()
        self.server_thread.join()

    def test_crawl_one_url(self):
        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.crawler.crawl(url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 1)

        request, _ = self.http_traffic_queue.get()

        self.assertEqual(request.get_url().url_string, url)

    def test_crawl_xmlhttprequest(self):
        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=XmlHttpRequestHandler)

        self.server_thread = t
        self.server = s
        self.server_port = p

        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one sent using XMLHttpRequest
        request, _ = self.http_traffic_queue.get()

        root_url = URL(root_url)
        server_url = root_url.url_join('/server')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)


class XmlHttpRequestHandler(InstrumentedChromeHandler):

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
