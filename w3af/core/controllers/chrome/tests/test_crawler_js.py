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
from w3af.core.controllers.chrome.tests.test_instrumented import ExtendedHttpRequestHandler
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.parsers.doc.url import URL


class TestChromeCrawlerClick(unittest.TestCase):
    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def _unittest_setup(self, request_handler_klass):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

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

    def test_crawl_xmlhttprequest(self):
        self._unittest_setup(XmlHttpRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _ = self.http_traffic_queue.get()

        root_url = URL(root_url)
        server_url = root_url.url_join('/server')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)

    def test_crawl_full_page_reload(self):
        self._unittest_setup(TwoPagesRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one triggered after clicking on the div tag
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url + 'after-click')

    def test_crawl_full_page_reload_and_xmlhttprequest(self):
        self._unittest_setup(TwoPagesAndXmlHttpRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 3)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one triggered after clicking on the div tag
        # that does a full page reload
        request, _ = self.http_traffic_queue.get()
        self.assertEqual(request.get_url().url_string, root_url + 'after-click')

        # The third request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _ = self.http_traffic_queue.get()

        root_url = URL(root_url)
        server_url = root_url.url_join('/server')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)


class XmlHttpRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '''<html>
                       <script>
                           function sendRequest() {
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
                           } 
                       </script>
                       
                       <div onclick="sendRequest();">Click me</div>
                       
                       </html>'''


class TwoPagesRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY_ROOT = ('''<div onclick="goto();">This can be clicked</div>

                             <script>
                                 function goto() {
                                     document.location = '/after-click';
                                 }                           
                             </script>''')

    RESPONSE_BODY_CHANGED = '<body><p>DOM changed</p></body>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/after-click':
            return 200, self.RESPONSE_BODY_CHANGED


class TwoPagesAndXmlHttpRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY_ROOT = ('''<div onclick="goto();">This can be clicked</div>
    
                             <div onclick="sendRequest();">Click me</div>

                             <script>
                                 function goto() {
                                     document.location = '/after-click';
                                 }                           
                             </script>
                             
                             <script>
                                 function sendRequest() {
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
                                 } 
                             </script>
                             ''')

    RESPONSE_BODY_CHANGED = '<body><p>DOM changed</p></body>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/after-click':
            return 200, self.RESPONSE_BODY_CHANGED
