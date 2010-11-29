from pymock import PyMockTestCase, method, override
from time import time
import socket

from core.controllers.w3afException import w3afException, w3afMustStopException
from core.data.url.HTTPRequest import HTTPRequest
from core.data.url.handlers.keepalive import KeepAliveHandler, ConnectionManager,\
HTTPResponse, URLTimeoutError

class dummy: pass

class test_keepalive(PyMockTestCase):

    def setUp(self):
        # Setup objects
        PyMockTestCase.setUp(self)
        # The handler
        self.kahdler = KeepAliveHandler()
        self.kahdler._curr_check_failures = 1 # Only one timeout in-a-row
        # Host name
        self.host = 'host'
        # The connection
        self.conn = dummy()
        self.conn.is_fresh = 1
        self.conn.getresponse = 'blah'
        # The request obj mock
        self.req = self.mock()

    def test_get_and_remove_conn(self):
        '''
        Each requested connection must be closed by calling 'remove_connection'
        when the server doesn't support persistent HTTP Connections
        '''
        kah = self.kahdler
        host = self.host
        conn = self.conn
        req = self.req
        ## Start recording ##
        method(req, 'get_host').expects().returns(host)
        method(req, 'get_full_url').expects().returns('test_full_url')
        # Override KeepAliveHandler._start_transaction
        override(kah, '_start_transaction').expects(conn, req).returns(None)
        conn_factory = kah._get_connection
        # Mock conn's getresponse()
        resp = HTTPResponse(socket.socket())
        resp.will_close = True
        override(conn, 'getresponse').expects().returns(resp)
        # The connection mgr
        conn_mgr_mock = self.mock()
        method(conn_mgr_mock, 'get_available_connection').expects(host, conn_factory).returns(conn)
        method(conn_mgr_mock, 'remove_connection').expects(conn, host).returns(None)
        ## Stop Recording.Time to Play! ##
        self.replay()
        # Replace with mocked out ConnMgr.
        kah._cm = conn_mgr_mock
        kah.do_open(req)
        ## Verify ##
        self.verify()

    def test_timeout(self):
        """
        Ensure that kah raises 'URLTimeoutError' when timeouts occur and raises
        'w3afMustStopException' when the timeout limit is reached.
        """
        kah = self.kahdler
        host = self.host
        conn = self.conn
        req = self.req
        ## Start recording ##
        method(req, 'get_host').expects().returns(host)
        method(req, 'get_host').expects().returns(host)

        # Override KeepAliveHandler._start_transaction - raises timeout
        override(kah, '_start_transaction').expects(conn, req).raises(socket.timeout)
        conn_factory = kah._get_connection;
        # The connection mgr
        conn_mgr = self.mock()
        method(conn_mgr, 'get_available_connection').expects(host, conn_factory).returns(conn)
        method(conn_mgr, 'remove_connection').expects(conn, host).returns(None)
        ## Stop Recording.Time to Play! ##
        self.replay()
        # Replace with mocked out ConnMgr.
        kah._cm = conn_mgr
        self.assertRaises(URLTimeoutError, kah.do_open, req)
        self.assertRaises(w3afMustStopException, kah.do_open, req)
        ## Verify ##
        self.verify()

    def test_free_connection(self):
        """
        Ensure that conns are returned back to the pool when requests are
        closed.
        """
        override = self.override
        kah = self.kahdler
        conn = self.conn
        ## Start recording ##
        # The connection mgr
        conn_mgr = self.mock()
        override(conn_mgr, 'free_connection').expects(conn)
        ## Stop Recording.Time to Play! ##
        self.replay()
        kah._cm = conn_mgr
        kah._request_closed(conn)        
        ## Verify ##
        self.verify()
    
    def test_single_conn_mgr(self):
        '''
        We only want to use a single instance of the ConnectionManager.
        '''
        conn_mgr_id = id(self.kahdler._cm)
        import random
        for i in xrange(random.randint(1, 10)):
            self.assertTrue(conn_mgr_id == id(KeepAliveHandler()._cm))
        
        

class test_connection_mgr(PyMockTestCase):

    def setUp(self):
        PyMockTestCase.setUp(self)
        
        self.cm = ConnectionManager()
        self.host = dummy()
    
    def test_get_available_conn(self):
        '''
        Play with the pool, test, test... and test
        '''
        self.cm._host_pool_size = 1 # Only a single connection
        self.assertEquals(0, len(self.cm._hostmap))
        self.assertEquals(0, len(self.cm._used_cons))
        self.assertEquals(0, len(self.cm._free_conns))
        # Get connection
        cf = lambda h: dummy()
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
        t0 = time()
        self.assertRaises(w3afException, self.cm.get_available_connection, self.host, cf)
        self.assertTrue(time()-t0 >= 2.9, "Method returned before expected time")
    
    def test_replace_conn(self):
        cf = lambda h: dummy()
        bad_conn = dummy()
        self.assertRaises(ValueError, self.cm.replace_connection, bad_conn, self.host, cf)
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
        non_exist_conn = dummy()
        self.assertRaises(ValueError, self.cm.remove_connection, non_exist_conn)
        conn = self.cm.get_available_connection(self.host, lambda h: dummy())
        old_len = self.cm.get_connections_total()
        non_exist_host  = "non_host"
        self.assertRaises(ValueError, self.cm.remove_connection, conn, non_exist_host)
        # Remove ok
        self.cm.remove_connection(conn, self.host)
        # curr_len = old_len - 1
        self.assertTrue(old_len-1 == self.cm.get_connections_total() == 0)
        
        
        

        

if __name__=="__main__":
    import unittest
    unittest.main()
