"""
test_multipartpost.py

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

from w3af.core.data.dc.utils.multipart import multipart_encode
from w3af.core.controllers.misc.io import NamedStringIO


class TestMultipartEncode(unittest.TestCase):

    def test_encode_vars(self):
        _, encoded = multipart_encode([('a', 'b')], {}, boundary='fakeboundary')
        EXPECTED = '--fakeboundary\r\nContent-Disposition: form-data; name="a"'\
                   '\r\n\r\nb\r\n--fakeboundary--\r\n\r\n'
        self.assertEqual(EXPECTED, encoded)

    def test_encode_vars_files(self):
        _vars = [('a', 'b')]
        _files = [('file', NamedStringIO('file content', name='test.txt'))]

        _, encoded = multipart_encode(_vars, _files, boundary='fakeboundary')

        EXPECTED = '--fakeboundary\r\nContent-Disposition: form-data; name="a"'\
                   '\r\n\r\nb\r\n--fakeboundary\r\nContent-Disposition: form-data;'\
                   ' name="file"; filename="test.txt"\r\nContent-Type: text/plain'\
                   '\r\n\r\nfile content\r\n--fakeboundary--\r\n\r\n'
        self.assertEqual(EXPECTED, encoded)

    def test_encode_file_null(self):
        _files = [('file', NamedStringIO('\0hello world', name='test.txt'))]

        _, encoded = multipart_encode((), _files, boundary='fakeboundary')

        EXPECTED = '--fakeboundary\r\nContent-Disposition: form-data; name="file";'\
                   ' filename="test.txt"\r\nContent-Type: text/plain\r\n\r\n\x00'\
                   'hello world\r\n--fakeboundary--\r\n\r\n'
        self.assertEqual(EXPECTED, encoded)

    def test_encode_two_files(self):
        _files = [('file1', NamedStringIO('hello world', name='test1.txt')),
                  ('file2', NamedStringIO('bye bye', name='test2.txt'))]

        _, encoded = multipart_encode((), _files, boundary='fakeboundary')

        EXPECTED = '--fakeboundary\r\nContent-Disposition: form-data;' \
                   ' name="file1"; filename="test1.txt"\r\n' \
                   'Content-Type: text/plain\r\n\r\nhello world\r\n' \
                   '--fakeboundary\r\nContent-Disposition: form-data;' \
                   ' name="file2"; filename="test2.txt"\r\n' \
                   'Content-Type: text/plain\r\n\r\nbye bye\r\n' \
                   '--fakeboundary--\r\n\r\n'
        self.assertEqual(EXPECTED, encoded)
