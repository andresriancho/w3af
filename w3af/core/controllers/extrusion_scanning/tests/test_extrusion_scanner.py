"""
test_extrusion_scanner.py

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
import unittest
import commands

import w3af.core.data.kb.config as cf

from nose.plugins.attrib import attr
from w3af.core.controllers.extrusion_scanning.extrusionScanner import extrusionScanner
from w3af.plugins.tests.helper import onlyroot


class TestExtrusionScanner(unittest.TestCase):
    """
    Test the extrusion scanner's basic features.
    """
    def test_basic(self):
        es = extrusionScanner(commands.getoutput)

        self.assertTrue(es.can_scan())

        self.assertTrue(es.estimate_scan_time() >= 8)

        self.assertTrue(es.is_available(54545, 'tcp'))

    @onlyroot
    @attr('ci_fails')
    def test_scan(self):
        # FIXME: This unittest will only work in Linux
        cf.cf.save('interface', 'lo')
        cf.cf.save('local_ip_address', '127.0.0.1')
        es = extrusionScanner(commands.getoutput)

        inbound_port = es.get_inbound_port()
        self.assertEquals(inbound_port, 8080)

    def test_zzz(self):
        """
        Can't stop finding nosetests errors! It looks like SkipTest works except
        in the case where it is the last test discovered!
        """
        pass