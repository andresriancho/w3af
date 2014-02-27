"""
test_arp_cache.py

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


@attr('smoke')
class test_arp_cache(PayloadTestHelper):

    # Not used because I want to be less specific in this case
    EXPECTED_RESULT = {u'192.168.56.1': (u'0a:00:27:00:00:00', u'eth1'), }

    def test_arp_cache(self):
        result = exec_payload(self.shell, 'arp_cache', use_api=True)
        for ip_address, (mac, iface) in result.iteritems():
            self.assertEquals(ip_address.count('.'), 3)
            self.assertEquals(mac.count(':'), 5)
            self.assertTrue(iface.startswith('eth'))
