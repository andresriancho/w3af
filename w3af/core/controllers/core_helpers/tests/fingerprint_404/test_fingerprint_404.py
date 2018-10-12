# -*- coding: UTF-8 -*-
"""
test_fingerprint_404.py

Copyright 2014 Andres Riancho

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
from __future__ import division

import re
import random
import unittest

import httpretty

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.core_helpers.fingerprint_404 import Fingerprint404


class Generic404Test(unittest.TestCase):

    def get_body(self, unique_parts):
        parts = [re.__doc__, random.__doc__, unittest.__doc__]
        parts.extend(unique_parts)

        # Do not increase this 50 too much, it will exceed the xurllib max
        # HTTP response body length
        parts = parts * 50

        random.seed(1)
        random.shuffle(parts)

        body = '\n'.join(parts)
        return body

    def setUp(self):
        self.urllib = ExtendedUrllib()
        self.worker_pool = Pool(processes=2,
                                worker_names='WorkerThread',
                                max_queued_tasks=20,
                                maxtasksperchild=20)

        self.fingerprint_404 = Fingerprint404()
        self.fingerprint_404.set_url_opener(self.urllib)
        self.fingerprint_404.set_worker_pool(self.worker_pool)

    def tearDown(self):
        self.urllib.clear()
        self.worker_pool.terminate_join()


class Test404Detection(Generic404Test):

    @httpretty.activate
    def test_issue_3234(self):
        #
        # is_404 can not handle URLs with : in path #3234
        # https://github.com/andresriancho/w3af/issues/3234
        #
        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body="404 found", status=404)

        url = URL('http://w3af.com/d:a')
        resp = HTTPResponse(200, 'body', Headers(), url, url)

        self.assertFalse(self.fingerprint_404.is_404(resp))


class Test404FalseNegative(Generic404Test):

    @httpretty.activate
    def test_false_negative(self):
        server_error = ('500 error that does NOT\n'
                        'look like one\n'
                        'because we want to reproduce the bug\n')

        not_found = ('This is a 404\n'
                     'but it does NOT look like one\n'
                     'because we want to reproduce the bug\n')

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/foo/(.*)"),
                               body=server_error,
                               status=500)

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=not_found,
                               status=404)

        foo_url = URL('http://w3af.com/foo/phpinfo.php')
        headers = Headers([('Content-Type', 'text/html')])
        server_error_resp = HTTPResponse(500, server_error, headers, foo_url, foo_url)

        self.assertTrue(self.fingerprint_404.is_404(server_error_resp))


class Test404FalsePositiveLargeResponsesRandom(Generic404Test):

    def request_callback(self, request, uri, headers):
        unique_parts = ['The request failed',
                        'Come back later',
                        '%s' % random.randint(1, 99999)]
        body = self.get_body(unique_parts)
        return 200, headers, body

    @httpretty.activate
    def test_false_positive(self):

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=self.request_callback,
                               status=200)

        success_url = URL('http://w3af.com/fi/')

        unique_parts = ['Welcome to our site',
                        'Content is being loaded using async JS',
                        'Please wait...']
        body = self.get_body(unique_parts)
        headers = Headers([('Content-Type', 'text/html')])
        success_200 = HTTPResponse(200, body, headers, success_url, success_url)

        self.assertFalse(self.fingerprint_404.is_404(success_200))


class Test404FalsePositiveLargeResponsesEqual(Test404FalsePositiveLargeResponsesRandom):
    def request_callback(self, request, uri, headers):
        unique_parts = ['The request failed',
                        'Come back later']
        body = self.get_body(unique_parts)
        return 200, headers, body


class GenericIgnoredPartTest(Generic404Test):
    ALL_SAME_BODY = ('All filenames in this path return the same HTTP'
                     ' response body, but that does NOT mean that the'
                     ' URL is a 404.\n'
                     '\n'
                     'The URL is completely valid, but the last part,'
                     ' the filename, does not influence the HTTP response'
                     ' body in any way.\n'
                     '\n'
                     'Also, removing the filename will yield a completely'
                     ' different result, because the url-rewrite rule does'
                     ' NOT match for that URL and the page returns something'
                     ' completely different.'
                     '\n'
                     'Heavy url rewrite sites do this.\n'
                     '\n'
                     ':-S')

    def request_callback(self, request, uri, headers):

        if '/path1/path2/' in uri:
            body = self.ALL_SAME_BODY
        elif '/path1/' in uri:
            body = 'The second path controls the HTTP response body'
        else:
            raise RuntimeError('Should never reach this.')

        return 200, headers, body


class Test404HandleIgnoredFilename(GenericIgnoredPartTest):

    @httpretty.activate
    def test_handle_ignored_filename(self):

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=self.request_callback,
                               status=200)

        # This is the URL we found during crawling and want to know if is_404()
        query_url = URL('http://w3af.com/path1/path2/xyz123')
        headers = Headers([('Content-Type', 'text/html')])
        success_200 = HTTPResponse(200, self.ALL_SAME_BODY, headers, query_url, query_url)

        self.assertFalse(self.fingerprint_404.is_404(success_200))


class Test404HandleIgnoredPath(GenericIgnoredPartTest):

    @httpretty.activate
    def test_handle_ignored_path(self):

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=self.request_callback,
                               status=200)

        # This is the URL we found during crawling and want to know if is_404()
        query_url = URL('http://w3af.com/path1/path2/path3/')
        headers = Headers([('Content-Type', 'text/html')])
        success_200 = HTTPResponse(200, self.ALL_SAME_BODY, headers, query_url, query_url)

        self.assertFalse(self.fingerprint_404.is_404(success_200))


class Test404HandleIgnoredPathAndFilename(GenericIgnoredPartTest):

    @httpretty.activate
    def test_handle_ignored_path(self):

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=self.request_callback,
                               status=200)

        # This is the URL we found during crawling and want to know if is_404()
        query_url = URL('http://w3af.com/path1/path2/path3/xyz123')
        headers = Headers([('Content-Type', 'text/html')])
        success_200 = HTTPResponse(200, self.ALL_SAME_BODY, headers, query_url, query_url)

        self.assertFalse(self.fingerprint_404.is_404(success_200))


class Test404HandleIgnoredPathDeep(GenericIgnoredPartTest):

    @httpretty.activate
    def test_handle_ignored_path(self):

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body=self.request_callback,
                               status=200)

        # This is the URL we found during crawling and want to know if is_404()
        query_url = URL('http://w3af.com/path1/path2/path3/path4/path5/')
        headers = Headers([('Content-Type', 'text/html')])
        success_200 = HTTPResponse(200, self.ALL_SAME_BODY, headers, query_url, query_url)

        self.assertFalse(self.fingerprint_404.is_404(success_200))
