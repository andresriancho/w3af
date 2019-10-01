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
from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.crawler.strategies.js import ChromeCrawlerJS
from w3af.core.data.parsers.doc.url import URL


class TestChromeCrawlerClick(BaseChromeCrawlerTest):

    def test_crawl_xmlhttprequest(self):
        self._unittest_setup(XmlHttpRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 2)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get_nowait()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one sent using XMLHttpRequest which
        # is triggered when clicking on the div tag
        request, _ = self.http_traffic_queue.get_nowait()

        root_url = URL(root_url)
        server_url = root_url.url_join('/server')
        data = 'foo=bar&lorem=ipsum'

        self.assertEqual(request.get_uri().url_string, server_url.url_string)
        self.assertEqual(request.get_data(), data)

    def test_crawl_full_page_reload(self):
        self._unittest_setup(TwoPagesRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        self.assertEqual(self.http_traffic_queue.qsize(), 3)

        # The first request is to load the main page
        request, _ = self.http_traffic_queue.get_nowait()
        self.assertEqual(request.get_url().url_string, root_url)

        # The second request is the one triggered after clicking on the div tag
        request, _ = self.http_traffic_queue.get_nowait()
        self.assertEqual(request.get_url().url_string, root_url + 'after-click')

    def test_crawl_full_page_reload_and_xmlhttprequest(self):
        self._unittest_setup(TwoPagesAndXmlHttpRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        requested_urls = set()
        requested_data = set()

        while not self.http_traffic_queue.empty():
            request, _ = self.http_traffic_queue.get_nowait()

            requested_urls.add(request.get_url().url_string)
            requested_data.add(request.get_data())

        expected_urls = {root_url,
                         root_url + 'after-click',
                         root_url + 'server'}

        expected_data = {'',
                         'foo=bar&lorem=ipsum'}

        self.assertEqual(requested_urls, expected_urls)
        self.assertEqual(requested_data, expected_data)

    def test_multiple_xmlhttprequest_actions(self):
        self._unittest_setup(MultipleXmlHttpRequestHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        requested_urls = set()
        requested_data = set()

        while not self.http_traffic_queue.empty():
            request, _ = self.http_traffic_queue.get_nowait()

            requested_urls.add(request.get_url().url_string)
            requested_data.add(request.get_data())

        #
        # Note that the MultipleXmlHttpRequestHandler has 15 event handlers
        # attached to <div> tags, but in here we're only expecting
        # ChromeCrawlerJS.MAX_SIMILAR_EVENT_DISPATCH of those to be clicked
        #
        # This is a performance improvement to prevent us from clicking on tags
        # which are very similar and will:
        #
        #   * Slow the crawler down
        #
        #   * Not (most likely) not find any new information
        #
        expected_urls = {root_url}
        for i in xrange(ChromeCrawlerJS.MAX_SIMILAR_EVENT_DISPATCH):
            expected_urls.add('%sserver_%s' % (root_url, i))

        expected_data = {'',
                         'foo=bar&lorem=ipsum'}

        self.assertEqual(requested_urls, expected_urls)
        self.assertEqual(requested_data, expected_data)

    def test_xmlhttprequest_with_dom_modifications(self):
        self._unittest_setup(ModifyDOMHandler)
        root_url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)

        self.crawler.crawl(root_url, self.http_traffic_queue)

        requested_urls = set()
        requested_data = set()

        while not self.http_traffic_queue.empty():
            request, _ = self.http_traffic_queue.get_nowait()

            requested_urls.add(request.get_url().url_string)
            requested_data.add(request.get_data())

        expected_urls = {root_url,
                         root_url + 'server_1'}

        expected_data = {'',
                         'foo=bar&lorem=ipsum'}

        self.assertEqual(requested_urls, expected_urls)
        self.assertEqual(requested_data, expected_data)


class ModifyDOMHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '''<html>
                       <script>
                           function sendRequest(n) {
                               var xhr = new XMLHttpRequest();
                               xhr.open("POST", '/server_' + n, true);

                               //Send the proper header information along with the request
                               xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

                               xhr.onreadystatechange = function() {//Call a function when the state changes.
                                   if(this.readyState == XMLHttpRequest.DONE && this.status == 200) {
                                       // Request finished. Do processing here.
                                   }
                               }
                               xhr.send("foo=bar&lorem=ipsum");
                           } 
                           
                           function removeElement(){
                               var elem = document.getElementById('div-01');
                               elem.parentNode.removeChild(elem);
                           }
                       </script>

                       <div onclick="removeElement();">Click me</div>
                       <div onclick="sendRequest(1);" id="div-01">Click me</div>

                       </html>'''


class MultipleXmlHttpRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '''<html>
                       <script>
                           function sendRequest(n) {
                               var xhr = new XMLHttpRequest();
                               xhr.open("POST", '/server_' + n, true);

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

                       <div onclick="sendRequest(0);">Click me</div>
                       <div onclick="sendRequest(1);">Click me</div>
                       <div onclick="sendRequest(2);">Click me</div>
                       <div onclick="sendRequest(3);">Click me</div>
                       <div onclick="sendRequest(4);">Click me</div>
                       <div onclick="sendRequest(5);">Click me</div>
                       <div onclick="sendRequest(6);">Click me</div>
                       <div onclick="sendRequest(7);">Click me</div>
                       <div onclick="sendRequest(8);">Click me</div>
                       <div onclick="sendRequest(9);">Click me</div>
                       <div onclick="sendRequest(10);">Click me</div>
                       <div onclick="sendRequest(11);">Click me</div>
                       <div onclick="sendRequest(12);">Click me</div>
                       <div onclick="sendRequest(13);">Click me</div>
                       <div onclick="sendRequest(14);">Click me</div>

                       </html>'''


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

    RESPONSE_BODY_CHANGED = u'<html><head></head><body><p>DOM changed</p></body></html>'

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

    RESPONSE_BODY_CHANGED = u'<html><head></head><body><p>DOM changed</p></body></html>'

    def get_code_body(self, request_path):
        if request_path == '/':
            return 200, self.RESPONSE_BODY_ROOT
        elif request_path == '/after-click':
            return 200, self.RESPONSE_BODY_CHANGED
