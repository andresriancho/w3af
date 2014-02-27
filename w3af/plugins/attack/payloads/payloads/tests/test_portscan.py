"""
test_portscan.py

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
from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper_exec import PayloadTestHelperExec
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_portscan(PayloadTestHelperExec):

    RESULT_22 = {'localhost': ['22']}
    RESULT_23 = {'localhost': []}

    @attr('ci_fails')
    def test_portscan(self):
        result = exec_payload(self.shell, 'portscan',
                              args=('localhost', '22'),
                              use_api=True)
        self.assertEquals(self.RESULT_22, result)

        result = exec_payload(self.shell, 'portscan',
                              args=('localhost', '23'),
                              use_api=True)
        self.assertEquals(self.RESULT_23, result)