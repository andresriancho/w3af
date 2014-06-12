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

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.form import Form
from w3af.core.data.dc.multipart_container import MultipartContainer


@attr('smoke')
class TestMultipartContainer(unittest.TestCase):

    def test_multipart_post(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = 'multipart/form-data; boundary=%s'

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        mpc = MultipartContainer.from_postdata(headers, post_data)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertIn('a', mpc)
        self.assertEqual(mpc['a'], ['bcd'])
        self.assertEqual(mpc.get_file_vars(), [])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')

    def test_multipart_post_with_filename(self):
        fake_file = NamedStringIO('def', name='hello.txt')
        vars = [('a', 'bcd'), ]
        files = [('b', fake_file)]
        boundary, post_data = multipart_encode(vars, files)
        multipart_boundary = 'multipart/form-data; boundary=%s'

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

    def test_multipart_from_form(self):
        form = Form()

        form.add_input([('name', 'a'), ('type', 'text'),
                      ('value', 'bcd')])
        form.set_file_name('b', 'hello.txt')
        form.add_file_input([('name', 'b')])

        mpc = MultipartContainer.from_form(form)

        self.assertIsInstance(mpc, MultipartContainer)
        self.assertEqual(mpc['a'], ['bcd'])
        self.assertEqual(mpc.get_file_vars(), ['b'])
        self.assertEqual(mpc.get_parameter_type('a'), 'text')
        self.assertEqual(mpc.get_parameter_type('b'), 'file')
        self.assertEqual(mpc.get_file_name('b'), 'hello.txt')