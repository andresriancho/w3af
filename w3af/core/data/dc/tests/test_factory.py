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

from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.generic.plain import PlainContainer
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.dc.tests.test_xmlrpc import XML_WITH_FUZZABLE
from w3af.core.data.dc.tests.test_json_container import COMPLEX_OBJECT
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.fuzzer.form_filler import smart_fill_file
from w3af.core.data.dc.factory import (dc_from_hdrs_post,
                                       dc_from_form_params,
                                       dc_from_content_type_and_raw_params)


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

        self.assertIsInstance(dc, URLEncodedForm)
        self.assertIn('a', dc)
        self.assertIn('b', dc)
        self.assertEqual('a=3&b=2', str(dc))

    def test_unknown_default_form(self):
        headers = self.get_headers('foo/bar')
        dc = dc_from_hdrs_post(headers, 'a=3&b=2')

        self.assertIsInstance(dc, PlainContainer)
        self.assertEqual(headers.items(), dc.get_headers())
        self.assertEqual(str(dc), 'a=3&b=2')

    def test_unknown_default_form_no_urlencoded(self):
        headers = self.get_headers('foo/bar')
        dc = dc_from_hdrs_post(headers, 'a')

        self.assertIsInstance(dc, PlainContainer)
        self.assertEqual(headers.items(), dc.get_headers())
        self.assertEqual(str(dc), 'a')

    def test_dc_from_form_params_with_files(self):
        form_params = FormParameters()

        form_params.add_field_by_attr_items([('name', 'b'),
                                             ('type', 'file')])
        form_params.add_field_by_attr_items([('name', 'a'),
                                             ('type', 'text'),
                                             ('value', 'bcd')])
        form_params.set_file_name('b', 'hello.txt')

        mpdc = dc_from_form_params(form_params)

        self.assertIsInstance(mpdc, MultipartContainer)
        self.assertEqual(mpdc.get_file_vars(), ['b'])
        self.assertEqual(mpdc['a'], ['bcd'])

    def test_dc_from_form_params_without_files_with_multipart_enctype(self):
        form_params = FormParameters()
        form_params.set_method('POST')
        form_params.set_form_encoding('multipart/form-data')
        form_params.add_field_by_attr_items([('name', 'a'),
                                             ('type', 'text'),
                                             ('value', 'bcd')])

        mpdc = dc_from_form_params(form_params)

        self.assertIsInstance(mpdc, MultipartContainer)
        self.assertEqual(mpdc.get_file_vars(), [])
        self.assertEqual(mpdc['a'], ['bcd'])

    def test_dc_from_form_params_without_files_nor_enctype(self):
        form_params = FormParameters()

        form_params.add_field_by_attr_items([('name', 'a'),
                               ('type', 'text'),
                               ('value', 'bcd')])

        urlencode_dc = dc_from_form_params(form_params)

        self.assertIsInstance(urlencode_dc, URLEncodedForm)
        self.assertEqual(urlencode_dc.get_file_vars(), [])
        self.assertEqual(urlencode_dc['a'], ['bcd'])


class TestDCFactoryFromRawParams(unittest.TestCase):
    def test_json_simple(self):
        params = {'hello': 'world', 'bye': 0}
        dc = dc_from_content_type_and_raw_params('application/json', params)

        self.assertIsInstance(dc, JSONContainer)
        self.assertEqual(str(dc), json.dumps(params))

    def test_multipart_no_files(self):
        params = {'hello': 'world', 'bye': 'bye'}
        dc = dc_from_content_type_and_raw_params('multipart/form-data', params)

        self.assertIsInstance(dc, MultipartContainer)
        self.assertEqual(dc['hello'], ['world'])
        self.assertEqual(dc['bye'], ['bye'])

    def test_multipart_with_files(self):
        params = {'hello': 'world', 'file': smart_fill_file('image', 'cat.png')}
        dc = dc_from_content_type_and_raw_params('multipart/form-data', params)

        self.assertIsInstance(dc, MultipartContainer)
        self.assertEqual(dc['hello'], ['world'])
        self.assertIn('file', dc.get_file_vars())

    def test_urlencoded_form(self):
        params = {'hello': 'world', 'bye': 'bye'}
        dc = dc_from_content_type_and_raw_params('application/x-www-form-urlencoded', params)

        self.assertIsInstance(dc, URLEncodedForm)
        self.assertEqual(dc['hello'], ['world'])
        self.assertEqual(dc['bye'], ['bye'])
