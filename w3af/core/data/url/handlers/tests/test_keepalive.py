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
import psutil
import os

from mock import MagicMock, Mock
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.exceptions import BaseFrameworkException, ScanMustStopException
from w3af.core.data.url.handlers.keepalive import (KeepAliveHandler,
                                              ConnectionManager,
                                              HTTPResponse,
                                              URLTimeoutError,
                                              HTTPHandler, HTTPSHandler)


@attr('moth')
@attr('ci_ready')
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

        conn_factory = kah._get_connection
        # Mock conn's getresponse()
        resp = HTTPResponse(socket.socket())
        resp.will_close = True
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
        conn_mgr_mock.get_available_connection.assert_called_once_with(
            host, conn_factory)
        conn_mgr_mock.remove_connection.assert_called_once_with(conn, host)

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

        conn_factory = kah._get_connection

        # The connection mgr
        conn_mgr = Mock()
        conn_mgr.get_available_connection = MagicMock(return_value=conn)
        conn_mgr.remove_connection = MagicMock(return_value=None)

        # Replace with mocked out ConnMgr.
        kah._cm = conn_mgr
        self.assertRaises(URLTimeoutError, kah.do_open, req)
        self.assertRaises(ScanMustStopException, kah.do_open, req)

        kah._start_transaction.assert_called_once_with(conn, req)
        conn_mgr.get_available_connection.assert_called_once_with(
            host, conn_factory)
        conn_mgr.remove_connection.assert_called_once_with(conn, host)

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
        We only want to use different instances of the ConnectionManager for
        HTTP and HTTPS.
        """
        conn_mgr_http = id(HTTPHandler()._cm)
        conn_mgr_https = id(HTTPSHandler(':')._cm)
        
        self.assertNotEqual(conn_mgr_http,conn_mgr_https)
    
    
    def test_close_all_established_sockets(self):
        self.close_all_sockets(0)

    def test_close_all_close_wait_sockets(self):
        # Give the socket time to move to close_wait
        self.close_all_sockets(20)
        
    def close_all_sockets(self, wait):
        keep_alive_http = HTTPHandler()

        uri_opener = urllib2.build_opener(keep_alive_http)
        
        response = uri_opener.open(get_moth_http())
        html = response.read()

        time.sleep(wait)
        
        pid = os.getpid()
        p = psutil.Process(pid)
        connections_before = p.get_connections()
        
        keep_alive_http.close_all()
        
        connections_after = p.get_connections()
        
        self.assertLess(len(connections_after), len(connections_before))
        
        
class test_connection_mgr(unittest.TestCase):

    def setUp(self):
        self.cm = ConnectionManager()
        self.host = Mock()

    def test_get_available_conn(self):
        """
        Play with the pool, test, test... and test
        """
        self.cm._host_pool_size = 1  # Only a single connection
        self.assertEquals(0, len(self.cm._hostmap))
        self.assertEquals(0, len(self.cm._used_cons))
        self.assertEquals(0, len(self.cm._free_conns))
        # Get connection
        cf = lambda h: Mock()
        conn = self.cm.get_available_connection(self.host, cf)
        self.assertEquals(1, len(self.cm._hostmap))
        self.assertEquals(1, len(self.cm._used_cons))
        self.assertEquals(0, len(self.cm._free_conns))
        # Return it to the pool
        self.cm.free_connection(conn)
        self.assertEquals(1, len(self.cm._hostmap))
        self.assertEquals(0, len(self.cm._used_cons))
        self.assertEquals(1, len(self.cm._free_conns))
        # Ask for a conn again
        conn = self.cm.get_available_connection(self.host, cf)
        t0 = time.time()
        self.assertRaises(
            BaseFrameworkException, self.cm.get_available_connection, self.host, cf)
        self.assertTrue(
            time.time() - t0 >= 2.9, "Method returned before expected time")

    def test_replace_conn(self):
        cf = lambda h: Mock()
        bad_conn = Mock()
        self.assertRaises(
            ValueError, self.cm.replace_connection, bad_conn, self.host, cf)
        bad_conn = self.cm.get_available_connection(self.host, cf)
        old_len = self.cm.get_connections_total()
        # Replace bad with a new one
        new_conn = self.cm.replace_connection(bad_conn, self.host, cf)
        # Must be different conn objects
        self.assertNotEquals(bad_conn, new_conn)
        # The len must be the same
        self.assertEquals(self.cm.get_connections_total(), old_len)

    def test_remove_conn(self):
        # Rem a non existing conn
        non_exist_conn = Mock()
        conn = self.cm.get_available_connection(self.host, lambda h: Mock())
        old_len = self.cm.get_connections_total()
        non_exist_host = "non_host"
        self.assertRaises(
            ValueError, self.cm.remove_connection, conn, non_exist_host)
        # Remove ok
        self.cm.remove_connection(conn, self.host)
        # curr_len = old_len - 1
        self.assertTrue(old_len - 1 == self.cm.get_connections_total() == 0)
