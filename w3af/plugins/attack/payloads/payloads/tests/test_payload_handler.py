"""
test_payload_handler.py

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
import commands
import unittest
import os

from w3af.plugins.attack.payloads.payload_handler import (payload_to_file,
                                                     is_payload,
                                                     exec_payload,
                                                     runnable_payloads,
                                                     get_payload_instance,
                                                     get_payload_list)

from w3af import ROOT_PATH
from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.data.kb.read_shell import ReadShell
from w3af.core.data.kb.tests.test_vuln import MockVuln


class TestPayloadHandler(unittest.TestCase):

    def test_payload_to_file(self):
        cpu_info_file = payload_to_file('cpu_info')
        expected_file = os.path.join(ROOT_PATH,
                                     'plugins/attack/payloads/payloads/cpu_info.py')
        self.assertEqual(cpu_info_file, expected_file)

    def test_get_payload_list(self):
        payload_list = get_payload_list()

        KNOWN_NAMES = (
            'cpu_info',
            'arp_cache',
            'current_user',
            'users',
            'udp',
        )

        for known_name in KNOWN_NAMES:
            self.assertTrue(known_name in payload_list,
                            '%s not in %s' % (known_name, payload_list))

        self.assertTrue(len(payload_list), len(set(payload_list)))

        self.assertFalse('__init__' in payload_list)
        self.assertFalse('__init__.py' in payload_list)

    def test_get_payload_instance(self):
        shell = FakeExecShell()
        for payload_name in get_payload_list():
            payload_inst = get_payload_instance(payload_name, shell)

            self.assertTrue(payload_inst.require() in ('linux', 'windows'))

    def test_runnable_payloads_exec(self):
        shell = FakeExecShell()
        runnable = runnable_payloads(shell)

        EXCEPTIONS = set(['portscan', ])
        all_payloads = get_payload_list()
        all_but_exceptions = set(all_payloads) - EXCEPTIONS

        self.assertEquals(
            set(runnable),
            all_but_exceptions
        )

    def test_runnable_payloads_read(self):
        shell = FakeReadShell()
        runnable = runnable_payloads(shell)

        EXPECTED = (
            'apache_run_user', 'cpu_info', 'firefox_stealer', 'get_hashes')
        NOT_EXPECTED = (
            'msf_linux_x86_meterpreter_reverse_tcp', 'portscan', 'w3af_agent')

        for name in EXPECTED:
            self.assertTrue(name in runnable)

        for name in NOT_EXPECTED:
            self.assertFalse(name in runnable)

    def test_exec_payload_exec(self):
        shell = FakeExecShell()
        result = exec_payload(shell, 'os_fingerprint', use_api=True)
        self.assertEquals({'os': 'Linux'}, result)

    def test_exec_payload_read(self):
        shell = FakeReadShell()
        result = exec_payload(shell, 'os_fingerprint', use_api=True)
        self.assertEquals({'os': 'Linux'}, result)

        result = exec_payload(shell, 'cpu_info', use_api=True)
        # On my box the result is:
        #
        # {'cpu_info': 'AMD Phenom(tm) II X4 945 Processor', 'cpu_cores': '4'}
        #
        # But because others will also run this, I don't want to make it so
        # strict
        self.assertTrue('cpu_info' in result)
        self.assertTrue('cpu_cores' in result)
        self.assertGreater(int(result['cpu_cores']), 0)
        self.assertLess(int(result['cpu_cores']), 12)

    def test_is_payload(self):
        self.assertTrue(is_payload('cpu_info'))
        self.assertFalse(is_payload('andres_riancho'))


class FakeExecShell(ExecShell):
    # pylint: disable=E0202
    worker_pool = None
    
    def __init__(self):
        vuln = MockVuln()       
        super(FakeExecShell, self).__init__(vuln, None, None)
    
    def execute(self, command):
        return commands.getoutput(command)

    def end(self):
        pass

    def get_name(self):
        return 'FakeExecShell'


class FakeReadShell(ReadShell):

    worker_pool = None

    def __init__(self):
        vuln = MockVuln()       
        super(FakeReadShell, self).__init__(vuln, None, None)

    def read(self, filename):
        return file(filename).read()

    def end(self):
        pass

    def get_name(self):
        return 'FakeReadShell'
