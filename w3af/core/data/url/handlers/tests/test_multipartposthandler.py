"""
test_multipartposthandler.py

Copyright 2010 Andres Riancho

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
import os
import tempfile
import unittest
import urllib2

from nose.plugins.attrib import attr

from w3af.core.data.url.handlers.multipart import MultipartPostHandler, multipart_encode
from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.controllers.ci.moth import get_moth_http


@attr('moth')
class TestMultipartPostHandler(unittest.TestCase):

    MOTH_FILE_UP_URL = get_moth_http('/core/file_upload/upload.py')

    def setUp(self):
        self.opener = urllib2.build_opener(MultipartPostHandler)

    def test_file_upload(self):
        temp = tempfile.mkstemp(suffix=".tmp")
        os.write(temp[0], '!--file content--')
        data = {"MAX_FILE_SIZE": "10000",
                "uploadedfile": open(temp[1], "rb")}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data).read()
        self.assertIn('was successfully uploaded', resp)

    def test_file_upload2(self):
        # Basically the same test but with list as values
        temp = tempfile.mkstemp(suffix=".tmp")
        os.write(temp[0], '!--file content--')
        data = {"MAX_FILE_SIZE": ["10000"],
                "uploadedfile": [open(temp[1], "rb")]}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data).read()
        self.assertIn('was successfully uploaded', resp)

    def test_file_stringio_upload(self):
        data = {"MAX_FILE_SIZE": "10000",
                "uploadedfile": NamedStringIO('file content', name='test.txt')}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data)
        self.assertTrue('was successfully uploaded' in resp.read())

    def test_encode_vars(self):
        _, encoded = multipart_encode(
            [('a', 'b')], {}, boundary='fakeboundary')
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
