"""
test_parser_cache.py

Copyright 2012 Andres Riancho

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
import os
import time
import unittest
import multiprocessing

from mock import patch, call, PropertyMock

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.parser_cache import ParserCache
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.html import HTMLParser
from w3af.core.data.parsers.tests.test_document_parser import _build_http_response


class TestParserCache(unittest.TestCase):
    
    def setUp(self):
        self.url = URL('http://w3af.com')
        self.headers = Headers([(u'content-type', u'text/html')])
        self.dpc = ParserCache()

    def tearDown(self):
        self.dpc.stop_workers()

    def test_basic(self):
        resp1 = HTTPResponse(200, 'abc', self.headers, self.url, self.url)         
        resp2 = HTTPResponse(200, 'abc', self.headers, self.url, self.url)
        
        parser1 = self.dpc.get_document_parser_for(resp1)
        parser2 = self.dpc.get_document_parser_for(resp2)
        
        self.assertEqual(id(parser1), id(parser2))
    
    def test_bug_13_Dec_2012(self):
        url1 = URL('http://w3af.com/foo/')
        url2 = URL('http://w3af.com/bar/')
        body = '<a href="?id=1">1</a>'
        resp1 = HTTPResponse(200, body, self.headers, url1, url1)         
        resp2 = HTTPResponse(200, body, self.headers, url2, url2)
        
        parser1 = self.dpc.get_document_parser_for(resp1)
        parser2 = self.dpc.get_document_parser_for(resp2)
        
        self.assertNotEqual(id(parser1), id(parser2))
        
        _, parsed_refs_1 = parser1.get_references()
        _, parsed_refs_2 = parser2.get_references()
        
        self.assertEqual(parsed_refs_1, parsed_refs_2)
    
    def test_issue_188_invalid_url(self):
        # https://github.com/andresriancho/w3af/issues/188
        all_chars = ''.join([chr(i) for i in xrange(0, 255)])
        response = HTTPResponse(200, all_chars, self.headers, self.url, self.url)
        self.dpc.get_document_parser_for(response)

    def test_parser_timeout(self):
        """
        Test to verify fix for https://github.com/andresriancho/w3af/issues/6723
        "w3af running long time more than 24h"
        """
        modc = 'w3af.core.data.parsers.parser_cache.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(modc % 'om.out') as om_mock,\
             patch(modc % 'ParserCache.PARSER_TIMEOUT', new_callable=PropertyMock) as timeout_mock,\
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            #
            #   Test the timeout
            #
            html = '<html>DelayedParser!</html>'
            http_resp = _build_http_response(html, u'text/html')

            timeout_mock.return_value = 1
            parsers_mock.return_value = [DelayedParser, HTMLParser]

            try:
                self.dpc.get_document_parser_for(http_resp)
            except BaseFrameworkException:
                msg = '[timeout] The parser took more than %s seconds'\
                      ' to complete parsing of "%s", killed it!'

                error = msg % (ParserCache.PARSER_TIMEOUT,
                               http_resp.get_url())

                self.assertIn(call.debug(error), om_mock.mock_calls)
            else:
                self.assertTrue(False)

            #
            #   We now want to make sure that after we kill the process the Pool
            #   creates a new process for handling our tasks
            #
            #   https://github.com/andresriancho/w3af/issues/9713
            #
            html = '<html>foo-</html>'
            http_resp = _build_http_response(html, u'text/html')

            doc_parser = self.dpc.get_document_parser_for(http_resp)
            self.assertIsInstance(doc_parser._parser, HTMLParser)

    def test_daemon_child(self):
        """
        Reproduces:

            A "AssertionError" exception was found while running
            crawl.web_spider on "Method: GET | http://domain:8000/". The
            exception was: "daemonic processes are not allowed to have children"
            at process.py:start():124. The scan will continue but some
            vulnerabilities might not be identified.
        """
        queue = multiprocessing.Queue()

        p = multiprocessing.Process(target=daemon_child, args=(queue,))
        p.daemon = True
        p.start()
        p.join()

        got_assertion_error = queue.get(timeout=10)
        if got_assertion_error:
            self.assertTrue(False, 'daemonic processes are not allowed'
                                   ' to have children')

    def test_non_daemon_child_ok(self):
        """
        Making sure that the previous failure is due to "p.daemon = True"
        """
        queue = multiprocessing.Queue()

        p = multiprocessing.Process(target=daemon_child, args=(queue,))
        # This is where we change stuff:
        #p.daemon = True
        p.start()
        p.join()

        got_assertion_error = queue.get(timeout=10)
        if got_assertion_error:
            self.assertTrue(False, 'daemonic processes are not allowed'
                                   ' to have children')

    def test_dictproxy_pickle_8748(self):
        """
        MaybeEncodingError - PicklingError: Can't pickle dictproxy #8748
        https://github.com/andresriancho/w3af/issues/8748
        """
        html_body = os.path.join(ROOT_PATH, '/core/data/parsers/tests/data/',
                                 'pickle-8748.htm')

        url = URL('http://www.ensinosuperior.org.br/asesi.htm')
        resp = HTTPResponse(200, html_body, self.headers, url, url)

        parser = self.dpc.get_document_parser_for(resp)
        self.assertIsInstance(parser._parser, HTMLParser)


def daemon_child(queue):
    dpc = ParserCache()

    try:
        dpc.start_workers()
    except AssertionError:
        queue.put(True)
    else:
        queue.put(False)


class DelayedParser(object):
    def __init__(self, http_response):
        """
        According to the stopit docs it can't kill a thread running an
        atomic python function such as time.sleep() , so I have to
        create a function like this. I don't mind, since it's realistic
        with what we do in w3af anyways.
        """
        self.http_response = http_response

        total_delay = 3.0

        for _ in xrange(100):
            time.sleep(total_delay/100)

    @staticmethod
    def can_parse(http_response):
        return 'DelayedParser' in http_response.get_body()

    def clear(self):
        return True