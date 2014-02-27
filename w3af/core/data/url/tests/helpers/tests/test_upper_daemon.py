"""
test_upper_daemon.py

Copyright 2013 Andres Riancho

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

from w3af.core.data.url.tests.helpers.upper_daemon import UpperDaemon


class TestUpperDaemon(unittest.TestCase):
    """
    This is a unittest for the UpperDaemon which lives in upper_daemon.py
    
    @author: Andres Riancho <andres . riancho | gmail . com>
    """
    def setUp(self):
        self.upper_daemon = UpperDaemon()
        self.upper_daemon.start()
        self.upper_daemon.wait_for_start()
    
    def test_basic(self):
        sent = 'abc'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        sock.connect(('127.0.0.1', self.upper_daemon.get_port()))
        sock.sendall(sent)
        
        received = sock.recv(3)
        
        self.assertEqual(received, sent.upper())