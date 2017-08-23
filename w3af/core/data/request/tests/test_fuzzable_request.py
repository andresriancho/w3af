# -*- coding: utf-8 -*-
"""
test_fuzzablerequest.py

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
import cPickle
import copy

from nose.plugins.attrib import attr

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.factory import dc_from_form_params
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.dc.multipart_container import MultipartContainer


@attr('smoke')
class TestFuzzableRequest(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://w3af.com/a/b/c.php')

    def test_dump_case01(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hello: World',
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hello', u'World')])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected)

    def test_dump_case02(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: Múndo',
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hola', u'Múndo')])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected.encode('utf-8'))

    def test_dump_case03(self):
        header_value = ''.join(chr(i) for i in xrange(256))
        
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: %s' % smart_unicode(header_value),
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hola', header_value)])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected)

    def test_dump_mangle(self):
        fr = FuzzableRequest(URL('http://www.w3af.com/'),
                             headers=Headers([('Host', 'www.w3af.com')]))

        expected = u'\r\n'.join([u'GET http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u''])
        
        self.assertEqual(fr.dump(), expected)
        
        fr.set_method('POST')
        fr.set_data(KeyValueContainer(init_val=[('data', ['23'])]))
        
        expected = u'\r\n'.join([u'POST http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u'data=23'])
        
        self.assertEqual(fr.dump(), expected)

    def test_export_import_without_post_data(self):
        fr = FuzzableRequest(URL('http://www.w3af.com/'))

        imported_fr = FuzzableRequest.from_base64(fr.to_base64())
        self.assertEqual(imported_fr, fr)
    
    def test_export_import_with_post_data(self):
        dc = KeyValueContainer(init_val=[('a', ['1'])])
        fr = FuzzableRequest(URL('http://www.w3af.com/'), post_data=dc)

        imported_fr = FuzzableRequest.from_base64(fr.to_base64())
        self.assertEqual(imported_fr, fr)

    def test_equal(self):
        u = URL('http://www.w3af.com/')
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u)
        self.assertEqual(fr1, fr2)

        fr1 = FuzzableRequest(URL("http://www.w3af.com/a"))
        fr2 = FuzzableRequest(URL("http://www.w3af.com/b"))
        self.assertNotEqual(fr1, fr2)
        
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u, method='POST')
        self.assertNotEqual(fr1, fr2)
    
    def test_set_url(self):
        self.assertRaises(TypeError, FuzzableRequest, 'http://www.google.com/')
        
        url = URL('http://www.google.com/')
        r = FuzzableRequest(url)
        self.assertEqual(r.get_url(), url)

    def test_str_no_qs(self):
        fr = FuzzableRequest(URL('http://www.w3af.com/'))
        expected = 'Method: GET | http://www.w3af.com/'
        self.assertEqual(str(fr), expected)

    def test_str_qs(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/?id=3"))
        expected = 'Method: GET | http://www.w3af.com/ |' \
                   ' Query string: (id)'
        self.assertEqual(str(fr), expected)

    def test_str_with_postdata(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        fr = FuzzableRequest.from_parts('http://www.w3af.com/', post_data='a=1',
                                        headers=headers)
        expected = 'Method: GET | http://www.w3af.com/ | URL encoded ' \
                   'form: (a)'
        self.assertEqual(str(fr), expected)

    def test_str_with_qs_and_postdata(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        fr = FuzzableRequest.from_parts("http://www.w3af.com/?id=3",
                                        post_data='a=1&b=3&a=2',
                                        headers=headers)
        expected = 'Method: GET | http://www.w3af.com/ | URL encoded ' \
                   'form: (a, a, b)'
        self.assertEqual(str(fr), expected)

    def test_repr(self):
        url = 'http://www.w3af.com/'
        fr = FuzzableRequest(URL(url))

        self.assertEqual(repr(fr), '<fuzzable request | GET | %s>' % url)

    def test_sent_url_unicode_decode_1(self):
        f = FuzzableRequest(URL('http://example.com/a%c3%83b'))
        self.assertTrue(f.sent('aÃb'))

    def test_sent_url_unicode_decode_2(self):
        f = FuzzableRequest(URL('http://example.com/aÃb'))
        self.assertTrue(f.sent('aÃb'))

    def test_sent_url_unicode_decode_3(self):
        f = FuzzableRequest(URL('http://example.com/aÃb'))
        self.assertTrue(f.sent(u'aÃb'))

    def test_sent_headers(self):
        f = FuzzableRequest(URL('''http://example.com/'''),
                            headers=Headers([('User-Agent', 'payload')]))
        self.assertTrue(f.sent(u'payload'))

    def test_sent_headers_false(self):
        f = FuzzableRequest(URL('''http://example.com/'''),
                            headers=Headers([('User-Agent', 'payload')]))
        self.assertFalse(f.sent(u'payload-not-sent'))

    def test_sent_url(self):
        f = FuzzableRequest(URL('''http://example.com/a?p=d'z"0&paged=2'''))
        self.assertTrue(f.sent('d%5C%27z%5C%220'))

        f = FuzzableRequest(URL('http://example.com/a?p=<SCrIPT>alert("bsMs")'
                                '</SCrIPT>'))
        self.assertTrue(f.sent('<SCrIPT>alert(\"bsMs\")</SCrIPT>'))

        f = FuzzableRequest(URL('http://example.com/?p=<ScRIPT>a=/PlaO/%0A'
                                'fake_alert(a.source)</SCRiPT>'))
        self.assertTrue(f.sent('<ScRIPT>a=/PlaO/fake_alert(a.source)</SCRiPT>'))

    def test_sent_post_data(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", """d'z"0""")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])

        form = dc_from_form_params(form_params)

        f = FuzzableRequest(URL('http://example.com/'), post_data=form)
        self.assertTrue(f.sent('d%5C%27z%5C%220'))

    def test_from_form_POST(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "abc")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.set_action(URL('http://example.com/?id=1'))
        form_params.set_method('post')

        form = dc_from_form_params(form_params)

        fr = FuzzableRequest.from_form(form)

        self.assertIs(fr.get_uri(), form.get_action())
        self.assertIs(fr.get_raw_data(), form)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertEqual(fr.get_uri().querystring, QueryString([('id', ['1'])]))

    def test_from_form_GET(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "abc")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.set_action(URL('http://example.com/'))
        form_params.set_method('GET')

        form = dc_from_form_params(form_params)
        fr = FuzzableRequest.from_form(form)

        expected_url = 'http://example.com/?username=abc&address='
        self.assertEqual(fr.get_uri().url_string, expected_url)
        self.assertEqual(fr.get_uri().querystring, 'username=abc&address=')
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsNot(fr.get_raw_data(), form)
        self.assertIsInstance(fr.get_uri().querystring, URLEncodedForm)

        uri_1 = fr.get_uri()
        uri_2 = fr.get_uri()
        self.assertIs(uri_1, uri_2)

    def test_from_form_default(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "abc")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.set_action(URL('http://example.com/'))
        # Without a method
        #form_params.set_method('GET')

        form = dc_from_form_params(form_params)
        fr = FuzzableRequest.from_form(form)

        expected_url = 'http://example.com/?username=abc&address='
        self.assertEqual(fr.get_uri().url_string, expected_url)
        self.assertEqual(fr.get_uri().querystring, 'username=abc&address=')
        self.assertIsInstance(fr.get_uri().querystring, URLEncodedForm)
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsNot(fr.get_raw_data(), form)

    def test_pickle(self):
        fr = self.create_simple_fuzzable_request()

        unpickled_fr = cPickle.loads(cPickle.dumps(fr))
        self.assertEqual(fr, unpickled_fr)

    def test_deepcopy(self):
        fr = self.create_simple_fuzzable_request()

        fr_copy = copy.deepcopy(fr)

        self.assertEqual(fr, fr_copy)
        self.assertEqual(fr.get_uri(), fr_copy.get_uri())
        self.assertEqual(fr.get_headers(), fr_copy.get_headers())
        self.assertEqual(fr.get_data(), fr_copy.get_data())

        self.assertIsNot(fr, fr_copy)
        self.assertIsNot(fr.get_querystring(), fr_copy.get_querystring())
        self.assertIsNot(fr.get_uri(), fr_copy.get_uri())

    def create_simple_fuzzable_request(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "abc")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.set_action(URL('http://example.com/?id=1'))
        form_params.set_method('post')

        form = dc_from_form_params(form_params)

        return FuzzableRequest.from_form(form)
    
    def test_multipart_fuzzable_request_store(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        dc = MultipartContainer.from_postdata(headers, post_data)
        post_data = str(dc)

        fr = FuzzableRequest.from_parts(URL('http://www.w3af.com/'),
                                        method='POST', post_data=post_data,
                                        headers=headers)
        
        disk_set = DiskSet()
        disk_set.add(fr)

        fr_read = disk_set[0]

        self.assertIsInstance(fr_read.get_raw_data(), MultipartContainer)
        self.assertIn('a', fr_read.get_raw_data())
