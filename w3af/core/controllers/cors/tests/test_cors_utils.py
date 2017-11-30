# -*- encoding: utf-8 -*-
"""
test_utils.py

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
import unittest

from mock import MagicMock, Mock

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.cors.utils import (build_cors_request,
                                              retrieve_cors_header,
                                              provides_cors_features)


class TestUtils(unittest.TestCase):

    def test_provides_cors_features_fails(self):
        self.assertRaises(AttributeError, provides_cors_features, None, None, None)

    def test_provides_cors_features_false(self):
        url = URL('http://moth/')
        fr = FuzzableRequest(url)

        http_response = HTTPResponse(200, '', Headers(), url, url)

        url_opener_mock = Mock()
        url_opener_mock.GET = MagicMock(return_value=http_response)

        cors = provides_cors_features(fr, url_opener_mock, None)

        call_header = Headers({'Origin': 'www.w3af.org'}.items())
        url_opener_mock.GET.assert_called_with(url, headers=call_header)

        self.assertFalse(cors)

    def test_provides_cors_features_true(self):
        url = URL('http://moth/')
        fr = FuzzableRequest(url)

        hdrs = {'Access-Control-Allow-Origin': 'http://www.w3af.org/'}.items()
        cors_headers = Headers(hdrs)
        http_response = HTTPResponse(200, '', cors_headers, url, url)

        url_opener_mock = Mock()
        url_opener_mock.GET = MagicMock(return_value=http_response)

        cors = provides_cors_features(fr, url_opener_mock, None)

        url_opener_mock.GET.assert_called_with(url, debugging_id=None)

        self.assertTrue(cors)

    def test_retrieve_cors_header_true(self):
        url = URL('http://moth/')

        w3af_url = 'http://www.w3af.org/'
        hrds = {'Access-Control-Allow-Origin': w3af_url}.items()
        cors_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', cors_headers, url, url)

        value = retrieve_cors_header(http_response,
                                     'Access-Control-Allow-Origin')

        self.assertEqual(value, w3af_url)

    def test_retrieve_cors_header_false(self):
        url = URL('http://moth/')

        cors_headers = Headers({'Access-Control': 'Allow-Origin'}.items())
        http_response = HTTPResponse(200, '', cors_headers, url, url)

        value = retrieve_cors_header(http_response,
                                     'Access-Control-Allow-Origin')

        self.assertEqual(value, None)

    def test_build_cors_request_true(self):
        url = URL('http://moth/')

        fr = build_cors_request(url, 'http://foo.com/')

        self.assertEquals(fr.get_url(), url)
        self.assertEquals(fr.get_method(), 'GET')
        self.assertEquals(fr.get_headers(),
                          Headers({'Origin': 'http://foo.com/'}.items()))

    def test_build_cors_request_false(self):
        url = URL('http://moth/')

        fr = build_cors_request(url, None)

        self.assertEquals(fr.get_url(), url)
        self.assertEquals(fr.get_method(), 'GET')
        self.assertEquals(fr.get_headers(), Headers())
