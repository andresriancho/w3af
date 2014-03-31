"""
test_svn_config_files.py

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
from nose.plugins.attrib import attr

from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper import PayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_svn_config_files(PayloadTestHelper):

    @attr('ci_fails')
    def test_svn_config_files(self):
        result = exec_payload(self.shell, 'svn_config_files', use_api=True)
        self.assertTrue('/home/moth/.subversion/config' in result)
        self.assertTrue('props' in result['/home/moth/.subversion/config'])
