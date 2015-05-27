"""
test_create_fuzzable_request.py

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

from nose.plugins.attrib import attr

from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.generic.plain import PlainContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.request.factory import create_fuzzable_request_from_request
from w3af.core.data.request.fuzzable_request import FuzzableRequest


@attr('smoke')
class TestCreateFuzzableRequestFromParts(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')

    def test_simplest(self):
        fr = FuzzableRequest.from_parts(self.url)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), Headers())
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsInstance(fr.get_raw_data(), KeyValueContainer)

    def test_raw_url(self):
        raw_url = 'http://w3af.org/foo/'
        fr = FuzzableRequest.from_parts(raw_url)

        self.assertEqual(fr.get_url().url_string, raw_url)
        self.assertEqual(fr.get_headers(), Headers())
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsInstance(fr.get_raw_data(), KeyValueContainer)

    def test_headers(self):
        hdr = Headers([('foo', 'bar')])
        fr = FuzzableRequest.from_parts(self.url, headers=hdr)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsInstance(fr.get_raw_data(), KeyValueContainer)

    def test_headers_method(self):
        hdr = Headers([('foo', 'bar')])
        fr = FuzzableRequest.from_parts(self.url, method='PUT', headers=hdr)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'PUT')
        self.assertIsInstance(fr.get_raw_data(), KeyValueContainer)

    def test_simple_post(self):
        post_data = 'a=b&d=3'
        hdr = Headers([('content-length', str(len(post_data))),
                       ('content-type', URLEncodedForm.ENCODING)])

        fr = FuzzableRequest.from_parts(self.url, headers=hdr,
                                        post_data=post_data, method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIn('content-type', fr.get_headers())
        self.assertIsInstance(fr.get_raw_data(), URLEncodedForm)

    def test_json_post(self):
        post_data = '{"1":"2"}'
        hdr = Headers([('content-length', str(len(post_data))),
                       ('content-type', 'application/json')])

        fr = FuzzableRequest.from_parts(self.url, headers=hdr,
                                        post_data=post_data, method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIsInstance(fr.get_raw_data(), JSONContainer)

    def test_json_creation_missing_header(self):
        post_data = '{"1":"2"}'
        # Missing the content-type header for json
        headers = Headers([('content-length', str(len(post_data)))])

        fr = FuzzableRequest.from_parts(self.url, headers=headers,
                                        post_data=post_data, method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), headers)
        self.assertEqual(fr.get_method(), 'POST')

        # Here the "default" post-data is set, which will be empty because we
        # failed to parse the post-data
        self.assertIsInstance(fr.get_raw_data(), PlainContainer)
        self.assertEqual(fr.get_raw_data().get_param_names(), [])

    def test_xmlrpc_post(self):
        post_data = """<methodCall>
            <methodName>system.listMethods</methodName>
            <params></params>
        </methodCall>"""

        headers = Headers([('content-length', str(len(post_data)))])

        fr = FuzzableRequest.from_parts(self.url, headers=headers,
                                        post_data=post_data, method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), headers)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIsInstance(fr.get_raw_data(), XmlRpcContainer)

    def test_multipart_post(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = 'multipart/form-data; boundary=%s'

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        fr = FuzzableRequest.from_parts(self.url, headers=headers,
                                        post_data=post_data, method='POST')

        form_params = FormParameters()
        form_params.add_field_by_attr_items([('name', 'a'),
                               ('type', 'text'),
                               ('value', 'bcd')])

        expected_container = MultipartContainer(form_params)
        expected_headers = Headers([('content-type',
                                     multipart_boundary % boundary)])

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), expected_headers)
        self.assertIn('multipart/form-data', fr.get_headers()['content-type'])
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIsInstance(fr.get_raw_data(), MultipartContainer)
        self.assertEqual(fr.get_raw_data(), expected_container)

    def test_invalid_multipart_post(self):
        _, post_data = multipart_encode([('a', 'bcd'), ], [])

        # It is invalid because there is a missing boundary parameter in the
        # content-type header
        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', 'multipart/form-data')])

        fr = FuzzableRequest.from_parts(self.url, headers=headers,
                                        post_data=post_data, method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), headers)
        self.assertEqual(fr.get_method(), 'POST')

        # Here the "default" post-data is set, which will be empty because we
        # failed to parse the post-data
        self.assertIsInstance(fr.get_raw_data(), PlainContainer)
        self.assertEqual(fr.get_raw_data().get_param_names(), [])


@attr('smoke')
class TestCreateFuzzableRequestRequest(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')

    def test_from_HTTPRequest(self):
        request = HTTPRequest(self.url)
        fr = create_fuzzable_request_from_request(request)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_method(), 'GET')

    def test_from_HTTPRequest_headers(self):
        hdr = Headers([('Foo', 'bar')])
        request = HTTPRequest(self.url, headers=hdr)
        fr = create_fuzzable_request_from_request(request)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsInstance(fr, FuzzableRequest)
        self.assertIsInstance(fr.get_raw_data(), KeyValueContainer)
