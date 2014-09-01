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

from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.core_helpers.fingerprint_404 import (fingerprint_404,
                                                                is_404,
                                                                fingerprint_404_singleton)


class TestGenerate404Filename(unittest.TestCase):
    def test_404_generation(self):
        TESTS = [('ab-23', 'ba-23'),
                 ('abc-12', 'bac-21'),
                 ('ab-23.html', 'ba-23.html'),
                 ('a1a2', 'd4d5'),
                 ('a1a2.html', 'd4d5.html'),
                 ('Z', 'c'), # overflow handling
                 ('hello.html', 'ehllo.html'),
                 ]

        f404 = fingerprint_404()
        for fname, modfname in TESTS:
            self.assertEqual(f404._generate_404_filename(fname), modfname)


class Test404Detection(unittest.TestCase):

    @httpretty.activate
    def test_3234(self):
        """
        is_404 can not handle URLs with : in path #3234

        :see: https://github.com/andresriancho/w3af/issues/3234
        """
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
        self.assertFalse(db._is_404_with_extra_request(resp, 'body'))