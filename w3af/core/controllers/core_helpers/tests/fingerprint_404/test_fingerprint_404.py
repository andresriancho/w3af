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
import unittest

import httpretty

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.misc.generate_404_filename import generate_404_filename
from w3af.core.controllers.core_helpers.fingerprint_404 import (Fingerprint404,
                                                                fingerprint_404_singleton)


class TestGenerate404Filename(unittest.TestCase):
    def test_404_generation(self):
        tests = [
            ('ab-23', 'ba-23'),
            ('abc-12', 'bac-21'),
            ('ab-23.html', 'ba-23.html'),
            ('a1a2', 'd4d5'),
            ('a1a2.html', 'd4d5.html'),
            ('Z', 'c'), # overflow handling
            ('hello.html', 'ehllo.html'),
            ('r57_Mohajer22.php', 'r57_oMahejr22.php'),
        ]

        for fname, modfname in tests:
            self.assertEqual(generate_404_filename(fname), modfname)


class Test404Detection(unittest.TestCase):

    @httpretty.activate
    def test_3234(self):
        #
        # is_404 can not handle URLs with : in path #3234
        # https://github.com/andresriancho/w3af/issues/3234
        #
        # setup
        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body="404 found", status=404)

        url = URL('http://w3af.com/d:a')
        resp = HTTPResponse(200, 'body', Headers(), url, url)

        # setup, just to make some config settings values default
        core = w3afCore()
        core.scan_start_hook()

        # test
        db = fingerprint_404_singleton()
        self.assertFalse(db._is_404_with_extra_request(resp, 'body', None))


class Test404FalseNegative(unittest.TestCase):

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

        root_url = URL('http://w3af.com/')

        foo_url = URL('http://w3af.com/foo/phpinfo.php')
        server_error_resp = HTTPResponse(500, server_error, Headers(), foo_url, foo_url)

        urllib = ExtendedUrllib()
        worker_pool = Pool(processes=2,
                           worker_names='WorkerThread',
                           max_queued_tasks=2,
                           maxtasksperchild=20)

        fingerprint_404 = Fingerprint404()
        fingerprint_404.set_url_opener(urllib)
        fingerprint_404.set_worker_pool(worker_pool)
        fingerprint_404.generate_404_knowledge(root_url)

        self.assertTrue(fingerprint_404.is_404(server_error_resp))

        fingerprint_404.cleanup()
        urllib.clear()
        #worker_pool.terminate_join()

