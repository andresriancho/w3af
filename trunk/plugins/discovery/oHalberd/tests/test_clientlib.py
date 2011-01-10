# -*- coding: iso-8859-1 -*-

"""Unit tests for Halberd.clientlib
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import unittest
import urlparse

import Halberd.clientlib as clientlib

# TODO - Implement an HTTPServer so the test suite doesn't need to connect to
# external hosts.
# This HTTPServer must be bound only to localhost (for security reasons).
# TODO - Think about something similar for HTTPS.

class TestHTTPClient(unittest.TestCase):

    def setUp(self):
        self.client = clientlib.HTTPClient()

    def testGetHostAndPort(self):
        self.failUnlessEqual(self.client._getHostAndPort('localhost:8080'),
                             ('localhost', 8080))

        self.failUnlessEqual(self.client._getHostAndPort('localhost'),
                             ('localhost', self.client.default_port))

        self.assertRaises(clientlib.InvalidURL,
                          self.client._getHostAndPort, 'localhost:abc')

    def testFillTemplate(self):
        def get_request(url):
            scheme, netloc, url, params, query, fragment = \
                urlparse.urlparse(url)
            hostname, port = self.client._getHostAndPort(netloc)
            return self.client._fillTemplate(hostname, port, url,
                                             params, query, fragment)

        req = get_request('http://www.example.com:23/test?blop=777')
        self.failUnless(req.splitlines()[:2] == \
                        ['GET /test?blop=777 HTTP/1.1',
                         'Host: www.example.com:23'])

        req = get_request('http://www.example.com/test;blop?q=something')
        self.failUnless(req.splitlines()[:2] == \
                        ['GET /test;blop?q=something HTTP/1.1',
                         'Host: www.example.com'])

        req = get_request('http://localhost:8080')
        self.failUnless(req.splitlines()[0] == 'GET / HTTP/1.1')

    def testAntiCache(self):
        req = self.client._fillTemplate('localhost', 80, '/index.html')
        self.failUnless(req.splitlines()[2:4] == \
                        ['Pragma: no-cache', 'Cache-control: no-cache'])

    def testSendRequestSanityCheck(self):
        self.failUnlessRaises(clientlib.InvalidURL,
                              self.client._putRequest, '127.0.0.1',
                                                       'gopher://blop')

    def testSendRequestToLocal(self):
        try:
            self.client._putRequest('127.0.0.1', 'http://localhost:8000')
        except clientlib.ConnectionRefused:
            return

    def testSendRequestToRemote(self):
        self.client._putRequest('66.35.250.203', 'http://www.sourceforge.net')
        timestamp, headers = self.client._getReply()
        self.failUnless(headers and headers.startswith('HTTP/'))

    def testGetHeaders(self):
        addr, url = '66.35.250.203', 'http://www.sourceforge.net'
        reply = self.client.getHeaders(addr, url)
        self.failUnless(reply != (None, None))

    def testIncorrectReading(self):
        """Check for bug in _getReply (issue 60)
        Incorrect reading procedure in Halberd.clientlib.HTTPClient._getReply
        """
        self.client.bufsize = 1
        self.client.timeout = 10
        addr, url = '127.0.0.1', 'http://localhost'
        self.client._putRequest(addr, url)
        try:
            timestamp, headers = self.client._getReply()
        except clientlib.TimedOut, msg:
            self.fail('Timed out while trying to read terminator')
        self.failUnless(headers)


class TestHTTPSClient(unittest.TestCase):

    def setUp(self):
        self.client = clientlib.HTTPSClient()
        
    def testGetHostAndPort(self):
        self.failUnlessEqual(self.client._getHostAndPort('secure'),
                             ('secure', self.client.default_port))

        self.failUnlessEqual(self.client._getHostAndPort('secure:777'),
                             ('secure', 777))

    def testConnect(self):
        clientlib.HTTPSClient()._connect(('www.sourceforge.net', 443))

    def testInvalidConnect(self):
        self.failUnlessRaises(clientlib.HTTPSError,
                              clientlib.HTTPSClient()._connect,
                              ('localhost', 80))

        # XXX For better testing a keyfile and a certificate should be used.

    def testSendRequestToRemote(self):
        self.client._putRequest('66.35.250.203', 'https://www.sourceforge.net')
        timestamp, headers = self.client._getReply()
        self.failUnless(headers is not None and headers.startswith('HTTP/'))


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
