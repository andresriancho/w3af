"""
test_webserver.py

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
import urllib2
import unittest
import tempfile
import os

from w3af.core.controllers.daemons.webserver import (start_webserver,
                                                start_webserver_any_free_port)
from w3af.core.data.constants.ports import REMOTEFILEINCLUDE


class TestWebserver(unittest.TestCase):

    IP = '127.0.0.1'
    PORT = REMOTEFILEINCLUDE
    TESTSTRING = 'abc<>def'

    def setUp(self):
        self.tempdir = tempfile.gettempdir()
        
        for port in xrange(self.PORT, self.PORT + 15):
            try:
                self.server = start_webserver(self.IP, port, self.tempdir)
            except:
                pass
            else:
                self.PORT = port
                break

    def test_GET_404(self):
        # Raises a 404
        self.assertRaises(urllib2.HTTPError, urllib2.urlopen,
                          'http://%s:%s' % (self.IP, self.PORT))

    def _create_file(self):
        # Create a file and request it
        test_fh = file(os.path.join(self.tempdir, 'foofile.txt'), 'w')
        test_fh.write(self.TESTSTRING)
        test_fh.close()

    def test_is_down(self):
        # pylint: disable=E1103
        self.assertFalse(self.server.is_down())
        # pylint: enable=E1103

    def test_GET_exists(self):
        self._create_file()

        url = 'http://%s:%s/foofile.txt' % (self.IP, self.PORT)
        response_body = urllib2.urlopen(url).read()
        
        self.assertEqual(response_body, self.TESTSTRING)
    
    def test_any_free_port(self):
        self._create_file()
        _, port = start_webserver_any_free_port(self.IP, self.tempdir)
        
        url = 'http://%s:%s/foofile.txt' % (self.IP, port)
        response_body = urllib2.urlopen(url).read()
        
        self.assertEqual(response_body, self.TESTSTRING)