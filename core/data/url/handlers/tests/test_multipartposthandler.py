"""
test_multipartposthandler.py

Copyright 2010 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

from ..MultipartPostHandler import MultipartPostHandler 
from core.controllers.misc.io import NamedStringIO

## IMPORTANT! This test requires HTTP access to MOTH ##

class TestMultipartPostHandler(unittest.TestCase):
    
    MOTH_FILE_UP_URL = 'http://moth/w3af/audit/file_upload/uploader.php'

    def setUp(self):
        self.opener = urllib2.build_opener(MultipartPostHandler)

    def test_file_upload(self):
        temp = tempfile.mkstemp(suffix=".tmp")
        os.write(temp[0], '!--file content--')
        data = {"MAX_FILE_SIZE": "10000",
                "uploadedfile": open(temp[1], "rb")}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data).read()
        self.assertTrue('was successfully uploaded' in resp,
                        'Response was:\n%s' % resp)
    
    def test_file_upload2(self):
        # Basically the same test but with list as values
        temp = tempfile.mkstemp(suffix=".tmp")
        os.write(temp[0], '!--file content--')
        data = {"MAX_FILE_SIZE": ["10000"],
                "uploadedfile": [open(temp[1], "rb")]}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data).read()
        self.assertTrue('was successfully uploaded' in resp,
                        'Response was:\n%s' % resp)
    
    def test_file_stringio_upload(self):
        data = {"MAX_FILE_SIZE": "10000",
                "uploadedfile": NamedStringIO('file content', name='test.txt')}
        resp = self.opener.open(self.MOTH_FILE_UP_URL, data)
        self.assertTrue('was successfully uploaded' in resp.read())
    