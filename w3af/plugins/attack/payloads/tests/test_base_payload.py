"""
test_Payload.py

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

from mock import MagicMock

from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.plugins.attack.payloads.payloads.tests.test_payload_handler import (FakeReadShell,
                                                                         FakeExecShell)


class TestBasePayload(unittest.TestCase):
    
    def setUp(self):
        self.bp = Payload(FakeReadShell())
    
    def test_can_run(self):
        self.assertEqual(self.bp.can_run(), set())
    
    def test_run_only_read(self):
        bp = Payload(FakeReadShell())
        self.assertRaises(AttributeError, bp.run, 'filename')

    def test_run_execute(self):
        class Executable(Payload):
            called_run_execute = False
            called_api_execute = False
            
            def run_execute(self, cmd):
                self.called_run_execute = True
                self.shell.execute(cmd)

            def api_execute(self, cmd):
                self.called_api_execute = True
        
        shell = FakeExecShell()
        shell.execute = MagicMock(return_value='')
        
        executable = Executable(shell)
        
        self.assertEqual(self.bp.can_run(), set())
        
        executable.run('command')
        self.assertTrue(executable.called_run_execute)
        self.assertEqual(executable.shell.execute.call_count, 1)

        executable.run_api('command')
        self.assertTrue(executable.called_api_execute)
        