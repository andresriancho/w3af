"""
test_mp_document_parser.py

Copyright 2015 Andres Riancho

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
import random
import unittest
import multiprocessing

from mock import patch, PropertyMock
from nose.plugins.skip import SkipTest
from concurrent.futures import TimeoutError

from w3af import ROOT_PATH
from w3af.core.data.parsers.doc.sgml import Tag
from w3af.core.data.parsers.mp_document_parser import MultiProcessingDocumentParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.tests.test_document_parser import _build_http_response


class TestMPDocumentParser(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://w3af.com')
        self.headers = Headers([(u'content-type', u'text/html')])
        self.mpdoc = MultiProcessingDocumentParser()

    def tearDown(self):
        self.mpdoc.stop_workers()

    def test_basic(self):
        resp = HTTPResponse(200, '<a href="/abc">hello</a>',
                            self.headers, self.url, self.url)

        parser = self.mpdoc.get_document_parser_for(resp)

        parsed_refs, _ = parser.get_references()
        self.assertEqual([URL('http://w3af.com/abc')], parsed_refs)

    def test_no_parser_for_images(self):
        body = ''
        url = URL('http://w3af.com/foo.jpg')
        headers = Headers([(u'content-type', u'image/jpeg')])
        resp = HTTPResponse(200, body, headers, url, url)

        try:
            self.mpdoc.get_document_parser_for(resp)
        except Exception, e:
            self.assertEqual(str(e), 'There is no parser for images.')
        else:
            self.assertTrue(False, 'Expected exception!')

    def test_parser_timeout(self):
        """
        Test to verify fix for https://github.com/andresriancho/w3af/issues/6723
        "w3af running long time more than 24h"
        """
        mmpdp = 'w3af.core.data.parsers.mp_document_parser.%s'
        kmpdp = mmpdp % 'MultiProcessingDocumentParser.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(mmpdp % 'om.out') as om_mock,\
             patch(kmpdp % 'PARSER_TIMEOUT', new_callable=PropertyMock) as timeout_mock,\
             patch(kmpdp % 'MAX_WORKERS', new_callable=PropertyMock) as max_workers_mock,\
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            #
            #   Test the timeout
            #
            html = '<html>DelayedParser!</html>'
            http_resp = _build_http_response(html, u'text/html')

            timeout_mock.return_value = 1
            max_workers_mock.return_value = 1
            parsers_mock.return_value = [DelayedParser, HTMLParser]

            try:
                self.mpdoc.get_document_parser_for(http_resp)
            except TimeoutError, toe:
                self._is_timeout_exception_message(toe, om_mock, http_resp)
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

            doc_parser = self.mpdoc.get_document_parser_for(http_resp)
            self.assertIsInstance(doc_parser._parser, HTMLParser)

    def test_many_parsers_timing_out(self):
        """
        Received more reports of parsers timing out, and after that
        w3af showing always "The parser took more than X seconds to complete
        parsing of" for all calls to the parser.

        Want to test how well the the parser recovers from many timeouts.
        """
        mmpdp = 'w3af.core.data.parsers.mp_document_parser.%s'
        kmpdp = mmpdp % 'MultiProcessingDocumentParser.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(mmpdp % 'om.out') as om_mock,\
             patch(kmpdp % 'PARSER_TIMEOUT', new_callable=PropertyMock) as timeout_mock,\
             patch(kmpdp % 'MAX_WORKERS', new_callable=PropertyMock) as max_workers_mock,\
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            # Prepare the HTTP responses
            html_trigger_delay = '<html>DelayedParser!</html>%s'
            html_ok = '<html>foo-</html>%s'

            # Mocks
            timeout_mock.return_value = 1
            max_workers_mock.return_value = 5
            parsers_mock.return_value = [DelayedParser, HTMLParser]

            ITERATIONS = 25

            #
            # Lets timeout many sequentially
            #
            for i in xrange(ITERATIONS):
                http_resp = _build_http_response(html_trigger_delay % i, u'text/html')

                try:
                    self.mpdoc.get_document_parser_for(http_resp)
                except TimeoutError, toe:
                    self._is_timeout_exception_message(toe, om_mock, http_resp)
                else:
                    self.assertTrue(False)

            #
            # Lets timeout randomly
            #
            for i in xrange(ITERATIONS):
                html = random.choice([html_trigger_delay, html_ok])
                http_resp = _build_http_response(html % i, u'text/html')

                try:
                    parser = self.mpdoc.get_document_parser_for(http_resp)
                except TimeoutError, toe:
                    self._is_timeout_exception_message(toe, om_mock, http_resp)
                else:
                    self.assertIsInstance(parser._parser, HTMLParser)

            #
            # Lets parse things we know should work
            #
            for i in xrange(ITERATIONS):
                http_resp = _build_http_response(html_ok % i, u'text/html')
                parser = self.mpdoc.get_document_parser_for(http_resp)
                self.assertIsInstance(parser._parser, HTMLParser)

    def test_parser_with_large_attr_killed_when_sending_to_queue(self):
        """
        https://docs.python.org/2/library/multiprocessing.html

            Warning If a process is killed using Process.terminate()
            or os.kill() while it is trying to use a Queue, then the
            data in the queue is likely to become corrupted. This may
            cause any other process to get an exception when it tries
            to use the queue later on.

        Try to kill the process while it is sending data to the queue
        """
        raise SkipTest('This test breaks the build because it uses A LOT'
                       ' of memory, for more information take a look at'
                       ' https://circleci.com/gh/andresriancho/w3af/2819 .'
                       ' Note that there is no memory leak here, just a'
                       ' test which is designed to use a lot of memory'
                       ' to force a specific state.')

        mmpdp = 'w3af.core.data.parsers.mp_document_parser.%s'
        kmpdp = mmpdp % 'MultiProcessingDocumentParser.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(mmpdp % 'om.out') as om_mock,\
             patch(kmpdp % 'PARSER_TIMEOUT', new_callable=PropertyMock) as timeout_mock,\
             patch(kmpdp % 'MAX_WORKERS', new_callable=PropertyMock) as max_workers_mock,\
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            # Prepare the HTTP responses
            html_trigger_delay = '<html>HugeClassAttrValueParser!</html>%s'
            html_ok = '<html>foo-</html>%s'

            # Mocks
            timeout_mock.return_value = 1
            max_workers_mock.return_value = 5
            parsers_mock.return_value = [HugeClassAttrValueParser, HTMLParser]

            ITERATIONS = 10

            #
            # Lets timeout many sequentially
            #
            for i in xrange(ITERATIONS):
                http_resp = _build_http_response(html_trigger_delay % i, u'text/html')

                try:
                    self.mpdoc.get_document_parser_for(http_resp)
                except TimeoutError, toe:
                    self._is_timeout_exception_message(toe, om_mock, http_resp)
                else:
                    self.assertTrue(False)

            #
            # Lets timeout randomly
            #
            for i in xrange(ITERATIONS):
                html = random.choice([html_trigger_delay, html_ok])
                http_resp = _build_http_response(html % i, u'text/html')

                try:
                    parser = self.mpdoc.get_document_parser_for(http_resp)
                except TimeoutError, toe:
                    self._is_timeout_exception_message(toe, om_mock, http_resp)
                else:
                    self.assertIsInstance(parser._parser, HTMLParser)

            #
            # Lets parse things we know should work
            #
            for i in xrange(ITERATIONS):
                http_resp = _build_http_response(html_ok % i, u'text/html')
                parser = self.mpdoc.get_document_parser_for(http_resp)
                self.assertIsInstance(parser._parser, HTMLParser)

    def test_parser_memory_usage_exceeded(self):
        """
        This makes sure that we stop parsing a document that exceeds our memory
        usage limits.
        """
        mmpdp = 'w3af.core.data.parsers.mp_document_parser.%s'
        kmpdp = mmpdp % 'MultiProcessingDocumentParser.%s'
        modp = 'w3af.core.data.parsers.document_parser.%s'

        with patch(mmpdp % 'om.out') as om_mock,\
             patch(kmpdp % 'MEMORY_LIMIT', new_callable=PropertyMock) as memory_mock,\
             patch(kmpdp % 'MAX_WORKERS', new_callable=PropertyMock) as max_workers_mock,\
             patch(modp % 'DocumentParser.PARSERS', new_callable=PropertyMock) as parsers_mock:

            #
            #   Test the memory usage
            #
            html = '<html>UseMemoryParser!</html>'
            http_resp = _build_http_response(html, u'text/html')

            memory_mock.return_value = 150000
            max_workers_mock.return_value = 1
            parsers_mock.return_value = [UseMemoryParser, HTMLParser]

            try:
                self.mpdoc.get_document_parser_for(http_resp)
            except MemoryError, me:
                self.assertIn('OOM issues', str(me))
            else:
                self.assertTrue(False)

            #
            # We now want to make sure that after we stop because of a memory issue
            # the process the Pool continues handling tasks as expected
            #
            html = '<html>foo-</html>'
            http_resp = _build_http_response(html, u'text/html')

            doc_parser = self.mpdoc.get_document_parser_for(http_resp)
            self.assertIsInstance(doc_parser._parser, HTMLParser)

    def _is_timeout_exception_message(self, toe, om_mock, http_resp):
        msg = ('[timeout] The parser took more than %s seconds to '
               'complete parsing of "%s", killed it!')

        error = msg % (MultiProcessingDocumentParser.PARSER_TIMEOUT,
                       http_resp.get_url())

        self.assertEquals(str(toe), error)

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

        parser = self.mpdoc.get_document_parser_for(resp)
        self.assertIsInstance(parser._parser, HTMLParser)

    def test_get_tags_by_filter(self):
        body = '<html><a href="/abc">foo</a><b>bar</b></html>'
        url = URL('http://www.w3af.com/')
        headers = Headers()
        headers['content-type'] = 'text/html'
        resp = HTTPResponse(200, body, headers, url, url, charset='utf-8')

        tags = self.mpdoc.get_tags_by_filter(resp, ('a', 'b'), yield_text=True)

        self.assertEqual([Tag('a', {'href': '/abc'}, 'foo'),
                          Tag('b', {}, 'bar')], tags)

    def test_get_tags_by_filter_empty_tag(self):
        body = '<html><script src="foo.js"></script></html>'
        url = URL('http://www.w3af.com/')
        headers = Headers()
        headers['content-type'] = 'text/html'
        resp = HTTPResponse(200, body, headers, url, url, charset='utf-8')

        tags = self.mpdoc.get_tags_by_filter(resp, ('script',), yield_text=True)

        # Note that lxml returns None for this tag text:
        self.assertEqual([Tag('script', {'src': 'foo.js'}, None)], tags)


def daemon_child(queue):
    dpc = MultiProcessingDocumentParser()

    try:
        dpc.start_workers()
    except AssertionError:
        queue.put(True)
    else:
        queue.put(False)


class DelayedParser(object):
    def __init__(self, http_response):
        self.http_response = http_response

    @staticmethod
    def can_parse(http_response):
        return 'DelayedParser' in http_response.get_body()

    def parse(self):
        time.sleep(3)

    def clear(self):
        return True


class UseMemoryParser(object):
    def __init__(self, http_response):
        self.http_response = http_response

    @staticmethod
    def can_parse(http_response):
        return 'UseMemoryParser' in http_response.get_body()

    def parse(self):
        memory_user = ''

        for _ in xrange(1000000):
            memory_user += 'A' * 256

    def clear(self):
        return True


class HugeClassAttrValueParser(object):
    parse_was_called = False

    def __init__(self, http_response):
        self.data_to_make_queue_busy = None
        self.http_response = http_response

    @staticmethod
    def can_parse(http_response):
        return 'HugeClassAttrValueParser' in http_response.get_body()

    def parse(self):
        self.data_to_make_queue_busy = 'A' * (2 ** 30)
        self.parse_was_called = True

    def clear(self):
        return True
