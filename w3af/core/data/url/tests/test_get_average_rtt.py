# -*- coding: utf-8 -*-
"""
test_get_average_rtt.py

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
import random
import unittest

import httpretty
from nose.plugins.attrib import attr

from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


@attr('smoke')
class TestGetAverageRTT(unittest.TestCase):

    MOCK_URL = 'http://www.w3af.org/'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()

    def tearDown(self):
        self.uri_opener.end()
        httpretty.reset()

    @httpretty.activate
    def test_get_average_rtt_for_mutant_all_equal(self):

        def request_callback(request, uri, headers):
            time.sleep(0.5)
            body = 'Yup'
            return 200, headers, body

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=request_callback)

        mock_url = URL(self.MOCK_URL)
        fuzzable_request = FuzzableRequest(mock_url)
        average_rtt = self.uri_opener.get_average_rtt_for_mutant(fuzzable_request)

        # Check the response
        self.assertGreater(average_rtt, 0.45)
        self.assertGreater(0.55, average_rtt)

    @httpretty.activate
    def test_get_average_rtt_for_mutant_similar(self):

        def request_callback(request, uri, headers):
            time.sleep(0.4 + random.randint(1, 9) / 100.0)
            body = 'Yup'
            return 200, headers, body

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=request_callback)

        mock_url = URL(self.MOCK_URL)
        fuzzable_request = FuzzableRequest(mock_url)
        average_rtt = self.uri_opener.get_average_rtt_for_mutant(fuzzable_request)

        # Check the response
        self.assertGreater(average_rtt, 0.45)
        self.assertGreater(0.55, average_rtt)

    @httpretty.activate
    def test_get_average_rtt_for_mutant_one_off(self):
        #
        # TODO: This is one of the cases I need to fix using _has_outliers!
        #       Calculating the average using 0.3 , 0.2 , 2.0 is madness
        #

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=RequestCallBackWithDelays([0.3, 0.2, 2.0]))

        mock_url = URL(self.MOCK_URL)
        fuzzable_request = FuzzableRequest(mock_url)
        average_rtt = self.uri_opener.get_average_rtt_for_mutant(fuzzable_request)

        # Check the response
        self.assertGreater(average_rtt, 0.80)
        self.assertGreater(0.90, average_rtt)


class RequestCallBackWithDelays(object):

    def __init__(self, delays):
        self.call = 0
        self.delays = delays

    def __call__(self, request, uri, headers):
        time.sleep(self.delays[self.call])
        self.call += 1

        body = 'Yup'
        return 200, headers, body
