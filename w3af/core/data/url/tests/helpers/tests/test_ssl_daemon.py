"""
test_ssl_daemon.py

Copyright 2015 Andres Riancho

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
import socket
import ssl

from w3af.core.data.url.tests.helpers.ssl_daemon import RawSSLDaemon


class TestUpperDaemon(unittest.TestCase):
    """
    This is a unittest for the UpperDaemon which lives in ssl_daemon.py

    @author: Andres Riancho <andres . riancho | gmail . com>
    """
    def setUp(self):
        self.ssl_daemon = RawSSLDaemon()
        self.ssl_daemon.start()
        self.ssl_daemon.wait_for_start()

    def test_basic(self):
        sent = 'abc'

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(sock)

        sock.connect(('127.0.0.1', self.ssl_daemon.get_port()))
        sock.sendall(sent)

        received = sock.recv(3)

        self.assertEqual(received, sent.upper())
