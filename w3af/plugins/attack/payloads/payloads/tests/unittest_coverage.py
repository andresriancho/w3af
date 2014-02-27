"""
unittest_coverage.py

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
import os
import unittest

from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

from w3af import ROOT_PATH
from w3af.plugins.attack.payloads.payload_handler import get_payload_list

PAYLOAD_PATH = os.path.join(ROOT_PATH, 'plugins', 'attack', 'payloads', 'payloads')
TEST_PATH = os.path.join(PAYLOAD_PATH, 'tests')

UNABLE_TO_TEST = ('metasploit', 'msf_linux_x86_meterpreter_reverse',
                  'msf_windows_meterpreter_reverse_tcp',
                  'msf_windows_vncinject_reverse')


@attr('smoke')
class TestUnittestCoverage(unittest.TestCase):

    def test_payloads(self):
        self._analyze_unittests()

    def test_nothing_in_unable_to_test(self):
        if len(UNABLE_TO_TEST) > 0:
            # TODO: In vdaemon.py we have subprocess.Popen( ['gnome-terminal', '-e', msfcli_command] )
            #       which makes the payloads in UNABLE_TO_TEST very very very difficult to test
            raise SkipTest()

    def _analyze_unittests(self):
        payloads = get_payload_list()

        missing = []

        for payload in payloads:
            if not self._has_test(payload):
                missing.append(payload)

        if missing:
            msg = 'The following payloads dont have unittests: %s' %  \
                  (', '.join(sorted(missing)))
            self.assertTrue(False, msg)

    def _has_test(self, payload_name):
        tests = os.listdir(TEST_PATH)
        fname = 'test_%s.py' % payload_name
        return fname in tests or payload_name in UNABLE_TO_TEST
