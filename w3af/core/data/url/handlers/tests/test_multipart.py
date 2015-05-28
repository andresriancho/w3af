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
import os
import tempfile
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.controllers.ci.moth import get_moth_http


@attr('moth')
class TestMultipartPostUpload(unittest.TestCase):
    """
    In the new architecture I've been working on, the HTTP requests are almost
    completely created by serializing two objects:
        * FuzzableRequest
        * DataContainer (stored in FuzzableRequest._post_data)

    There is a special DataContainer sub-class for MultipartPost file uploads
    called MultipartContainer, which holds variables and files and when
    serialized will be encoded as multipart.

    These test cases try to make sure that the file upload feature works by
    sending a POST request with a MultipartContainer to moth.
    """
    MOTH_FILE_UP_URL = URL(get_moth_http('/core/file_upload/upload.py'))

    def setUp(self):
        self.opener = ExtendedUrllib()

    def tearDown(self):
        self.opener.end()

    def test_multipart_without_file(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([('name', 'uploadedfile')])
        form_params['uploadedfile'][0] = 'this is not a file'
        form_params.add_field_by_attr_items([('name', 'MAX_FILE_SIZE'),
                       ('type', 'hidden'),
                       ('value', '10000')])

        mpc = MultipartContainer(form_params)

        resp = self.opener.POST(self.MOTH_FILE_UP_URL, data=str(mpc),
                                headers=Headers(mpc.get_headers()))

        self.assertNotIn('was successfully uploaded', resp.get_body())

    def test_file_upload(self):
        temp = tempfile.mkstemp(suffix=".tmp")
        os.write(temp[0], 'file content')

        _file = open(temp[1], "rb")
        self.upload_file(_file)

    def test_stringio_upload(self):
        _file = NamedStringIO('file content', name='test.txt')
        self.upload_file(_file)

    def upload_file(self, _file):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([('name', 'uploadedfile')])
        form_params.add_field_by_attr_items([('name', 'MAX_FILE_SIZE'),
                               ('type', 'hidden'),
                               ('value', '10000')])

        mpc = MultipartContainer(form_params)
        mpc['uploadedfile'][0] = _file

        resp = self.opener.POST(self.MOTH_FILE_UP_URL, data=str(mpc),
                                headers=Headers(mpc.get_headers()))

        self.assertIn('was successfully uploaded', resp.get_body())

    def test_upload_file_using_fuzzable_request(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([('name', 'uploadedfile')])
        form_params['uploadedfile'][0] = NamedStringIO('file content', name='test.txt')
        form_params.add_field_by_attr_items([('name', 'MAX_FILE_SIZE'),
                       ('type', 'hidden'),
                       ('value', '10000')])

        mpc = MultipartContainer(form_params)

        freq = FuzzableRequest(self.MOTH_FILE_UP_URL, post_data=mpc,
                               method='POST')

        resp = self.opener.send_mutant(freq)

        self.assertIn('was successfully uploaded', resp.get_body())

