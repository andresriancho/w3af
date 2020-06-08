"""
test_multipart.py

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
import copy
import os

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.dc.headers import Headers
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.multipart_container import MultipartContainer

MULTIPART_TEST = '''\
--4266ff2e00ac63588a571483e5727142
Content-Disposition: form-data; name="MAX_FILE_SIZE"

2097152
--4266ff2e00ac63588a571483e5727142
Content-Disposition: form-data; name="file"; filename="rsXiwMY.gif"
Content-Type: image/gif

GIF89aAAAAAAAAAAAAAAAAA;
--4266ff2e00ac63588a571483e5727142--
'''


@attr('smoke')
class TestMultipartContainer(unittest.TestCase):

    def test_multipart_post(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        mpc = MultipartContainer.from_postdata(headers, post_data)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('a', mpc)
        self.assertEqual(mpc['a'], ['bcd'])
        self.assertEqual(mpc.get_file_vars(), [])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')

    def test_multipart_post_empty_value(self):
        boundary, post_data = multipart_encode([('a', ''), ], [])
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        mpc = MultipartContainer.from_postdata(headers, post_data)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('a', mpc)
        self.assertEqual(mpc['a'], [''])
        self.assertEqual(mpc.get_file_vars(), [])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')

    def test_multipart_test_from_string(self):
        multipart_boundary = MultipartContainer.MULTIPART_HEADER
        boundary = '4266ff2e00ac63588a571483e5727142'

        headers = Headers([('content-length', str(len(MULTIPART_TEST))),
                           ('content-type', multipart_boundary % boundary)])

        mpc = MultipartContainer.from_postdata(headers, MULTIPART_TEST)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('MAX_FILE_SIZE', mpc)
        self.assertIn('file', mpc)

        self.assertEqual(mpc['MAX_FILE_SIZE'], ['2097152'])
        self.assertTrue(mpc['file'][0].startswith('GIF89'))

        self.assertEqual(mpc.get_file_vars(), ['file'])
        self.assertEqual(mpc.get_parameter_type('MAX_FILE_SIZE'), 'text')
        self.assertEqual(mpc.get_parameter_type('file'), 'file')
        self.assertEqual(mpc.get_file_name('file'), 'rsXiwMY.gif')

    def test_multipart_post_with_filename(self):
        fake_file = NamedStringIO('def', name='hello.txt')
        vars = [('a', 'bcd'), ]
        files = [('b', fake_file)]
        boundary, post_data = multipart_encode(vars, files)
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        mpc = MultipartContainer.from_postdata(headers, post_data)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('a', mpc)
        self.assertEqual(mpc['a'], ['bcd'])
        self.assertEqual(mpc.get_file_vars(), ['b'])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')
        self.assertEqual(mpc.get_parameter_type('b'), 'file')
        self.assertEqual(mpc.get_file_name('b'), 'hello.txt')

    def test_multipart_from_form_params(self):
        form_params = FormParameters()

        form_params.add_field_by_attr_items([('name', 'b'),
                                             ('type', 'file')])
        form_params.add_field_by_attr_items([('name', 'a'),
                                             ('type', 'text'),
                                             ('value', 'bcd')])
        form_params.set_file_name('b', 'hello.txt')

        mpc = MultipartContainer(form_params)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertEqual(mpc['a'], ['bcd'])
        self.assertEqual(mpc.get_file_vars(), ['b'])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')
        self.assertEqual(mpc.get_parameter_type('b'), 'file')
        self.assertEqual(mpc.get_file_name('b'), 'hello.txt')

    def test_multipart_3570(self):
        headers = Headers([(u'Content-length', u'557'),
                           (u'Accept-encoding', u'gzip, deflate'),
                           (u'Accept', u'*/*'),
                           (u'User-agent', u'Mozilla/4.0'),
                           (u'Host', u'www.webscantest.com'),
                           (u'Cookie', u'SESSIONID_VULN_SITE=k4no98smgdkun2eqme5k2btgb5'),
                           (u'Referer', u'http://www.webscantest.com/'),
                           (u'Content-type', u'multipart/form-data; boundary=db36a3a8bb45ec40c22301ffcaa98e05')])

        test_dir = os.path.dirname(os.path.realpath(__file__))
        post_data_file = os.path.join(test_dir, 'samples', 'post-data-3570')
        multipart_post_data = file(post_data_file).read()

        self.assertIn('db36a3a8bb45ec40c22301ffcaa98e05', multipart_post_data)
        self.assertEqual(len(multipart_post_data), 557)

        mpc = MultipartContainer.from_postdata(headers, multipart_post_data)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('MAX_FILE_SIZE', mpc)
        self.assertIn('userfile', mpc)

        self.assertEqual(mpc['MAX_FILE_SIZE'], ['2097152'])
        self.assertTrue(mpc['userfile'][0].startswith('GIF89'))

        self.assertEqual(mpc.get_file_vars(), ['userfile'])
        self.assertEqual(mpc.get_parameter_type('MAX_FILE_SIZE'), 'text')
        self.assertEqual(mpc.get_parameter_type('userfile'), 'file')
        self.assertEqual(mpc.get_file_name('userfile'), 'aTFiAgn.gif')

    def test_copy_with_token(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        dc = MultipartContainer.from_postdata(headers, post_data)

        dc.set_token(('a', 0))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())
        self.assertEqual(dc_copy.get_token().get_name(), 'a')

    def test_store_in_disk_set(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = MultipartContainer.MULTIPART_HEADER

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        dc = MultipartContainer.from_postdata(headers, post_data)

        dc.set_token(('a', 0))

        disk_set = DiskSet()
        disk_set.add(dc)

        dc_read = disk_set[0]

        # These are different objects
        self.assertIsNot(dc_read, dc)

        # But they hold the same data
        self.assertEqual(dc.get_token(), dc_read.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_read.get_token())
        self.assertEqual(dc_read.get_token().get_name(), 'a')
