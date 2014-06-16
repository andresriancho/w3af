# -*- coding: utf8 -*-
"""
test_factory.py

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
import unittest
import json

from w3af.core.data.dc.factory import dc_from_hdrs_post
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.dc.tests.test_xmlrpc import XML_WITH_FUZZABLE
from w3af.core.data.dc.tests.test_json_container import COMPLEX_OBJECT


class TestDCFactory(unittest.TestCase):
    def get_headers(self, content_type):
        return Headers(init_val=[('content-type', content_type)])

    def test_multipart(self):
        boundary, post_data = multipart_encode([('ax', 'bcd'), ], [])
        multipart_boundary = 'multipart/form-data; boundary=%s'

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        dc = dc_from_hdrs_post(headers, post_data)

        EXPECTED_PARAMS = [u'ax']

        self.assertIsInstance(dc, MultipartContainer)
        self.assertEqual(dc.get_param_names(), EXPECTED_PARAMS)

    def test_json(self):
        headers = self.get_headers('application/json')
        dc = dc_from_hdrs_post(headers, COMPLEX_OBJECT)

        EXPECTED_PARAMS = [u'object-second_key-list-0-string',
                           u'object-key-string']

        self.assertIsInstance(dc, JSONContainer)
        self.assertEqual(dc.get_param_names(), EXPECTED_PARAMS)
        self.assertEqual(json.loads(COMPLEX_OBJECT), json.loads(str(dc)))

    def test_xmlrpc(self):
        headers = self.get_headers('text/xml')
        dc = dc_from_hdrs_post(headers, XML_WITH_FUZZABLE)

        self.assertIsInstance(dc, XmlRpcContainer)
        self.assertIn('string', dc)
        self.assertIn('base64', dc)
        self.assertEqual(XML_WITH_FUZZABLE, str(dc))

    def test_form(self):
        headers = self.get_headers('application/x-www-form-urlencoded')
        dc = dc_from_hdrs_post(headers, 'a=3&b=2')

        self.assertIsInstance(dc, Form)
        self.assertIn('a', dc)
        self.assertIn('b', dc)
        self.assertEqual('a=3&b=2', str(dc))

    def test_unknown_default_form(self):
        headers = self.get_headers('foo/bar')
        dc = dc_from_hdrs_post(headers, 'a=3&b=2')

        self.assertIs(dc, None)

    def test_unknown_default_form_no_urlencoded(self):
        headers = self.get_headers('foo/bar')
        dc = dc_from_hdrs_post(headers, 'a')

        self.assertIs(dc, None)

    def test_dc_from_form_params_with_files(self):
        raise NotImplementedError

    def test_dc_from_form_params_without_files(self):
        raise NotImplementedError