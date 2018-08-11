"""
test_instrumented_event_listeners.py

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

import w3af.core.data.kb.config as cf

from w3af.core.controllers.output_manager import manager
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.chrome.crawler import ChromeCrawler
from w3af.core.controllers.chrome.tests.test_instrumented import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.instrumented import InstrumentedChrome
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.db.variant_db import PATH_MAX_VARIANTS
from w3af.core.data.parsers.doc.url import URL
from w3af.plugins.crawl.web_spider import web_spider


class TestChromeCrawlerGetEventListeners(unittest.TestCase):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def unittest_setup(self, request_handler_klass):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()

        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

        self.server_thread = t
        self.server = s
        self.server_port = p

        self.ic = InstrumentedChrome(self.uri_opener, self.http_traffic_queue)

        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        self.ic.load_url(url)

        self.ic.wait_for_load()

    def tearDown(self):
        while not self.http_traffic_queue.empty():
            self.http_traffic_queue.get()

        self.ic.terminate()
        self.server.shutdown()
        self.server_thread.join()

    def test_no_event_handlers_empty(self):
        self.unittest_setup(LinkTagRequestHandler)

        self.assertEqual(len(self.ic.get_event_listeners()), [])


class EmptyRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = ''


class LinkTagRequestHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '<a href="/">click</a>'
