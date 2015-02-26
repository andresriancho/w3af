"""
test_route.py

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


class test_route(PayloadTestHelper):

    # This is the output I got when I run it on my environment, but because
    # I want it to be more generic, I'll only use bits and pieces of this below
    EXPECTED_RESULT = {'route': [{'Destination': '0.0.0.0',
                                  'Gateway': '10.0.2.2',
                                  'Iface': 'eth0',
                                  'Mask': '0.0.0.0'},
                                 {'Destination': '10.0.2.0',
                                  'Gateway': '0.0.0.0',
                                  'Iface': 'eth0',
                                  'Mask': '255.255.255.0'},
                                 {'Destination': '192.168.56.0',
                                  'Gateway': '0.0.0.0',
                                  'Iface': 'eth1',
                                  'Mask': '255.255.255.0'}]}

    def test_route(self):
        result = exec_payload(self.shell, 'route', use_api=True)
        routes = result['route']

        for route_info in routes:
            dest = route_info['Destination']
            gw = route_info['Gateway']
            iface = route_info['Iface']
            mask = route_info['Mask']

            self.assertEqual(dest.count('.'), 3)
            self.assertEqual(gw.count('.'), 3)
            self.assertEqual(mask.count('.'), 3)
            
            self.assertTrue(iface.startswith('eth') or
                            iface.startswith('wlan') or
                            iface.startswith('ppp') or
                            iface.startswith('vbox') or
                            iface.startswith('lxcbr') or
                            iface.startswith('docker') or
                            iface.startswith('lo'), iface)
