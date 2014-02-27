"""
test_clientless_reverse_http.py

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
import socket
import tempfile
import unittest

import w3af.core.data.kb.config as cf

from nose.plugins.attrib import attr
from w3af.core.controllers.payload_transfer.clientless_reverse_http import ClientlessReverseHTTP
from w3af.core.controllers.extrusion_scanning.extrusionScanner import extrusionScanner
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.tests.helper import onlyroot


class TestClientlessReverseHTTP(unittest.TestCase):

    def get_usable_port(self, address):
        for listen_port in xrange(48488, 48497):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((address, listen_port))
            except socket.error:
                continue
            else:
                s.close()
                del s
                return listen_port

        return None

    def test_upload_file_mock(self):
        exec_method = commands.getoutput
        os = 'linux'

        create_temp_dir()
        cf.cf.save('interface', 'lo')
        cf.cf.save('local_ip_address', '127.0.0.1')
        inbound_port = self.get_usable_port('127.0.0.1')
        echo_linux = ClientlessReverseHTTP(exec_method, os, inbound_port)

        self.assertTrue(echo_linux.can_transfer())

        file_len = 8195
        file_content = 'A' * file_len
        echo_linux.estimate_transfer_time(file_len)

        temp_file_inst = tempfile.NamedTemporaryFile()
        temp_fname = temp_file_inst.name
        upload_success = echo_linux.transfer(file_content, temp_fname)

        self.assertTrue(upload_success)

    @onlyroot
    def test_upload_file_root(self):
        exec_method = commands.getoutput
        os = 'linux'

        create_temp_dir()
        cf.cf.save('interface', 'lo')
        cf.cf.save('local_ip_address', '127.0.0.1')
        es = extrusionScanner(exec_method)

        inbound_port = es.get_inbound_port()
        echo_linux = ClientlessReverseHTTP(exec_method, os, inbound_port)

        self.assertTrue(echo_linux.can_transfer())

        file_len = 8195
        file_content = 'A' * file_len
        echo_linux.estimate_transfer_time(file_len)

        temp_file_inst = tempfile.NamedTemporaryFile()
        temp_fname = temp_file_inst.name
        upload_success = echo_linux.transfer(file_content, temp_fname)

        self.assertTrue(upload_success)