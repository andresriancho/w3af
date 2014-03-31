"""
test_exec_methodHelpers.py

Copyright 2011 Andres Riancho

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

from mock import MagicMock

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.intrusion_tools.execMethodHelpers import (
    os_detection_exec,
    get_remote_temp_file)


class TestExecHelpers(unittest.TestCase):

    def test_os_detection_exec_linux(self):
        exec_method = commands.getoutput
        os = os_detection_exec(exec_method)
        self.assertEqual(os, 'linux')

    def test_os_detection_exec_windows(self):
        exec_method = MagicMock(
            side_effect=['Command not found', 'Command not found',
                         '[fonts]', 'ECHO'])
        os = os_detection_exec(exec_method)
        self.assertEqual(os, 'windows')

    def test_os_detection_exec_unknown(self):
        def side_effect(cmd):
            return 'foobarspameggs'

        exec_method = MagicMock(side_effect=side_effect)
        self.assertRaises(BaseFrameworkException, os_detection_exec, exec_method)

    def test_get_remote_temp_file_linux(self):
        exec_method = commands.getoutput
        tempfile = get_remote_temp_file(exec_method)
        self.assertTrue(tempfile.startswith('/tmp/'))

    def test_get_remote_temp_file_windows(self):
        exec_method = MagicMock(
            side_effect=['Command not found', 'Command not found',
                         '[fonts]', 'ECHO', 'C:\\Windows\\Temp\\',
                         'File not found'])
        tempfile = get_remote_temp_file(exec_method)
        self.assertTrue(tempfile.startswith('C:\\Windows\\Temp\\'))

    def test_get_remote_temp_file_unknown(self):
        def side_effect(cmd):
            return 'foobarspameggs'
        exec_method = MagicMock(side_effect=side_effect)
        self.assertRaises(BaseFrameworkException, get_remote_temp_file, exec_method)
