"""
test_uptime.py

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
from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper import PayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_uptime(PayloadTestHelper):

    # This is how it looks, but I want to have something generic so I don't use much
    # of this EXPECTED_RESULT dict, just the keys
    EXPECTED_RESULT = {'idletime': {'hours': '141', 'minutes': '43', 'seconds': '30'},
                       'uptime': {'hours': '144', 'minutes': '12', 'seconds': '2'}}

    def test_uptime(self):
        result = exec_payload(self.shell, 'uptime', use_api=True)

        for key in self.EXPECTED_RESULT:
            for time_unit in self.EXPECTED_RESULT[key]:
                self.assertTrue(
                    self.EXPECTED_RESULT[key][time_unit].isdigit())
