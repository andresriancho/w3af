"""
test_tcp.py

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


class TestTCP(PayloadTestHelper):

    EXPECTED_RESULT = {'172.18.0.9:8000', '0.0.0.0:8001', '0.0.0.0:8000'}

    def test_tcp(self):
        result = exec_payload(self.shell, 'tcp', use_api=True)

        local_addresses = []
        for key, conn_data in result.iteritems():
            local_addresses.append(conn_data['local_address'])

        local_addresses = set(local_addresses)

        for expected_local_address in self.EXPECTED_RESULT:
            self.assertIn(expected_local_address, local_addresses)
