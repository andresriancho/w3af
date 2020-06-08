"""
test_echo_linux.py

Copyright 2006 Andres Riancho

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
import tempfile

from w3af.core.controllers.payload_transfer.echo_linux import EchoLinux


class TestEchoLinux(unittest.TestCase):

    def test_upload_file(self):
        exec_method = commands.getoutput
        os = 'linux'
        echo_linux = EchoLinux(exec_method, os)

        self.assertTrue(echo_linux.can_transfer())

        file_len = 8195
        file_content = 'A' * file_len
        echo_linux.estimate_transfer_time(file_len)

        temp_file_inst = tempfile.NamedTemporaryFile()
        temp_fname = temp_file_inst.name
        upload_success = echo_linux.transfer(file_content, temp_fname)

        self.assertTrue(upload_success)
