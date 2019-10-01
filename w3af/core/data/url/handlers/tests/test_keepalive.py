"""
test_keepalive.py

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
import socket
import unittest
import time
import urllib2
import os

import psutil

from mock import MagicMock, Mock
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.handlers.keepalive import (KeepAliveHandler,
                                                   ConnectionManager,
                                                   HTTPResponse,
                                                   URLTimeoutError,
                                                   HTTPHandler, HTTPSHandler)


@attr('moth')
class TestKeepalive(unittest.TestCase):

    def setUp(self):
        # The handler
        self.kahdler = KeepAliveHandler()
        self.kahdler._curr_check_failures = 1  # Only one timeout in-a-row
        # Host name
        self.host = 'host'
        # The connection
        self.conn = Mock()
        self.conn.is_fresh = 1
        self.conn.getresponse = 'blah'
        # The request obj mock
        self.req = Mock()

    def test_get_and_remove_conn(self):
        """
        Each requested connection must be closed by calling 'remove_connection'
        when the server doesn't support persistent HTTP Connections
        """
        kah = self.kahdler
        host = self.host
        conn = self.conn
        req = self.req

        req.get_host = MagicMock(return_value=host)
        req.get_full_url = MagicMock(return_value='test_full_url')

        # Override KeepAliveHandler._start_transaction
        kah._start_transaction = MagicMock(return_value=None)

        conn_factory = kah.get_connection

        # Mock conn's getresponse()
        resp = HTTPResponse(socket.socket())
        resp.will_close = True
        resp.read = MagicMock(return_value='Response body')
        conn.getresponse = MagicMock(return_value=resp)

        # The connection mgr
        conn_mgr_mock = Mock()
        conn_mgr_mock.get_available_connection = MagicMock(return_value=conn)
        conn_mgr_mock.remove_connection = MagicMock(return_value=None)

        # Replace with mocked out ConnMgr.
        kah._cm = conn_mgr_mock
        kah.do_open(req)

        ## Verify ##
        kah._start_transaction.assert_called_once_with(conn, req)
        conn_mgr_mock.get_available_connection.assert_called_once_with(req,
                                                                       conn_factory)
        conn_mgr_mock.remove_connection.assert_called_once_with(conn,
                                                                reason='will close')

    def test_timeout(self):
        """
        Ensure that kah raises 'URLTimeoutError' when timeouts occur and raises
        'ScanMustStopException' when the timeout limit is reached.
        """
        kah = self.kahdler
        host = self.host
        conn = self.conn
        req = self.req

        req.get_host = MagicMock(side_effect=[host, host])

        # Override KeepAliveHandler._start_transaction - raises timeout
        kah._start_transaction = MagicMock(side_effect=socket.timeout())

        # The connection mgr
        conn_mgr = Mock()
        conn_mgr.get_available_connection = MagicMock(return_value=conn)
        conn_mgr.remove_connection = MagicMock(return_value=None)

        # Replace with mocked out ConnMgr
        kah._cm = conn_mgr

        # We raise URLTimeoutError each time the connection timeouts, the
        # keepalive handler doesn't take any decisions like
        # ScanMustStopByKnownReasonExc, which is the job of the extended urllib
        self.assertRaises(URLTimeoutError, kah.do_open, req)
        self.assertRaises(URLTimeoutError, kah.do_open, req)

        self.assertEqual(len(conn_mgr.get_available_connection.call_args_list), 2)
        self.assertEqual(len(conn_mgr.remove_connection.call_args_list), 3)

    def test_free_connection(self):
        """
        Ensure that conns are returned back to the pool when requests are
        closed.
        """
        kah = self.kahdler
        conn = self.conn

        # The connection mgr
        conn_mgr = Mock()
        conn_mgr.free_connection = MagicMock()

        kah._cm = conn_mgr
        kah._request_closed(conn)

        conn_mgr.free_connection.assert_called_once_with(conn)

    def test_single_conn_mgr(self):
        """
        We want to use different instances of the ConnectionManager for HTTP
        and HTTPS.
        """
        conn_mgr_http = HTTPHandler()._cm
        conn_mgr_https = HTTPSHandler(':')._cm
        
        self.assertIsNot(conn_mgr_http, conn_mgr_https)

    def test_close_all_established_sockets(self):
        self.close_all_sockets(0)

    def test_close_all_close_wait_sockets(self):
        # Give the socket time to move to close_wait
        self.close_all_sockets(20)
        
    def close_all_sockets(self, wait):
        keep_alive_http = HTTPHandler()

        uri_opener = urllib2.build_opener(keep_alive_http)

        request = HTTPRequest(URL(get_moth_http()))
        response = uri_opener.open(request)
        response.read()

        time.sleep(wait)

        # pylint: disable=E1101
        pid = os.getpid()
        p = psutil.Process(pid)
        connections_before = p.get_connections()
        
        keep_alive_http.close_all()

        time.sleep(1)
        connections_after = p.get_connections()
        # pylint: enable=E1101
        
        self.assertLess(len(connections_after), len(connections_before))
        
        
class TestConnectionMgr(unittest.TestCase):

    def setUp(self):
        self.cm = ConnectionManager()
        self.request = Mock()

    def test_get_available_conn_reuse(self):
        # We don't need a new HTTPConnection for each request
        self.request.new_connection = False
        self.request.get_host = lambda: 'w3af.org'
        self.request.get_netloc = lambda: 'w3af.org'

        self.cm.MAX_CONNECTIONS = 1  # Only a single connection
        self.assertEquals(0, len(self.cm._used_conns))
        self.assertEquals(0, len(self.cm._free_conns))

        # Get connection
        def conn_factory(request):
            mock = Mock()
            mock.host = request.get_host()
            mock.host_port = request.get_host()
            return mock

        conn_1 = self.cm.get_available_connection(self.request, conn_factory)
        self.assertEquals(1, len(self.cm._used_conns))
        self.assertEquals(0, len(self.cm._free_conns))

        # Return it to the pool
        self.cm.free_connection(conn_1)
        self.assertEquals(0, len(self.cm._used_conns))
        self.assertEquals(1, len(self.cm._free_conns))

        # Ask for a conn again, since we don't need a new connection, it should
        # return one from the pool
        conn_2 = self.cm.get_available_connection(self.request, conn_factory)
        self.assertIs(conn_2, conn_1)

    def test_get_available_conn_new_connection_requested(self):
        # We want a new HTTPConnection for each request
        self.request.new_connection = True

        self.cm.MAX_CONNECTIONS = 2
        self.assertEquals(0, len(self.cm._used_conns))
        self.assertEquals(0, len(self.cm._free_conns))

        # Get connection
        cf = lambda h: Mock()
        conn_1 = self.cm.get_available_connection(self.request, cf)
        self.assertEquals(1, len(self.cm._used_conns))
        self.assertEquals(0, len(self.cm._free_conns))

        # Return it to the pool
        self.cm.free_connection(conn_1)
        self.assertEquals(0, len(self.cm._used_conns))
        self.assertEquals(1, len(self.cm._free_conns))

        # Ask for another connection, it should return a new one
        conn_2 = self.cm.get_available_connection(self.request, cf)
        self.assertIsNot(conn_1, conn_2)

    def test_replace_conn(self):
        cf = lambda h: Mock()
        bad_conn = Mock()
        self.cm.replace_connection(bad_conn, self.request, cf)
        bad_conn = self.cm.get_available_connection(self.request, cf)
        old_len = self.cm.get_connections_total()

        # Replace bad with a new one
        new_conn = self.cm.replace_connection(bad_conn, self.request, cf)

        # Must be different conn objects
        self.assertNotEquals(bad_conn, new_conn)

        # The len must be the same
        self.assertEquals(self.cm.get_connections_total(), old_len)

    def test_remove_conn(self):
        self.assertEqual(self.cm.get_connections_total(), 0)

        conn = self.cm.get_available_connection(self.request, lambda h: Mock())
        self.assertEqual(self.cm.get_connections_total(), 1)

        self.cm.remove_connection(conn, reason='unittest')

        self.assertEqual(self.cm.get_connections_total(), 0)
