"""
test_get_source_code.py

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
import tempfile
import shutil

from nose.plugins.attrib import attr
from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper import PayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_get_source_code(PayloadTestHelper):

    EXPECTED_RESULT = {"https://moth/w3af/audit/local_file_read/local_file_read.php":
                       (
                       '/var/www/moth/w3af/audit/local_file_read/local_file_read.php',
                       'tmp__random__/var/www/moth/w3af/audit/local_file_read/local_file_read.php')
                       }

    CONTENT = "echo file_get_contents( $_REQUEST['file'] );"

    @attr('ci_fails')
    def test_get_source_code(self):
        temp_dir = tempfile.mkdtemp()
        result = exec_payload(self.shell, 'get_source_code', args=(temp_dir,),
                              use_api=True)

        self.assertEqual(len(self.EXPECTED_RESULT.keys()), 1)

        expected_url = self.EXPECTED_RESULT.keys()[0]
        downloaded_url = result.items()[0][0].url_string
        self.assertEquals(expected_url, downloaded_url)

        downloaded_file_path = result.items()[0][1][1]
        downloaded_file_content = file(downloaded_file_path).read()
        self.assertTrue(self.CONTENT in downloaded_file_content)

        shutil.rmtree(temp_dir)