"""
  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the
    Free Software Foundation, Inc.,
    59 Temple Place, Suite 330,
    Boston, MA  02111-1307  USA

This file is part of urlgrabber, a high-level cross-protocol url-grabber
Copyright 2002-2004 Michael D. Stenner, Ryan Tomayko

This file was modified (considerably) to be integrated with w3af. Some
modifications are:
  - Added the size limit for responses
  - Raising ConnectionPoolException in some places
  - Modified the HTTPResponse object in order to be able to perform multiple
    reads, and added a hack for the HEAD method.
  - SNI support for SSL
"""
import urllib2
import httplib
import operator
import socket
import threading
import time

import OpenSSL

from .utils import debug, error, to_utf8_raw
from .http_response import HTTPResponse
from .connections import (ProxyHTTPConnection, ProxyHTTPSConnection,
                          HTTPConnection, HTTPSConnection)
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              HTTPRequestException,
                                              ConnectionPoolException)


# Config
# Max connections allowed per host.
MAX_CONNECTIONS = 50


class URLTimeoutError(urllib2.URLError):
    """
    Our own URLError timeout exception. Basically a wrapper for socket.timeout.
    """
    def __init__(self):
        urllib2.URLError.__init__(self, (408, 'timeout'))

    def __str__(self):
        default_timeout = socket.getdefaulttimeout()
        if default_timeout is not None:
            return 'HTTP timeout error after %s seconds.' % default_timeout
        else:
            return 'HTTP timeout error.'


class ConnectionManager(object):
    """
    The connection manager must be able to:
        * keep track of all existing HTTPConnections
        * kill the connections that we're not going to use anymore
        * Create/reuse connections when needed.
        * Control the size of the pool.
    """
    # Used in get_available_connection
    GET_AVAILABLE_CONNECTION_RETRY_SECS = 0.25
    GET_AVAILABLE_CONNECTION_RETRY_NUM = 25

    def __init__(self):
        self._lock = threading.RLock()
        self._host_pool_size = MAX_CONNECTIONS
        self._hostmap = {}  # map hosts to a list of connections
        self._used_cons = []  # connections being used per host
        self._free_conns = []  # available connections

    def remove_connection(self, conn, host=None):
        """
        Remove a connection, it was closed by the server.

        :param conn: Connection to remove
        :param host: The host for to the connection. If passed, the connection
        will be removed faster.
        """
        # Just make sure we don't leak open connections
        conn.close()

        with self._lock:

            if host:
                if host in self._hostmap:
                    if conn in self._hostmap[host]:
                        self._hostmap[host].remove(conn)

            else:
                # We don't know the host. Need to find it by looping
                for _host, conns in self._hostmap.items():
                    if conn in conns:
                        host = _host
                        conns.remove(conn)
                        break

            for lst in (self._free_conns, self._used_cons):
                try:
                    lst.remove(conn)
                except ValueError:
                    # I don't care much about the connection not being in
                    # the free_conns or used_conns. This might happen because
                    # of a thread locking issue (basically, someone is not
                    # locking before moving connections around).
                    pass
            
            # No more conns for 'host', remove it from mapping
            conn_total = self.get_connections_total(host)
            if host and host in self._hostmap and not conn_total:
                del self._hostmap[host]
            
            msg = 'keepalive: removed one connection,' \
                  ' len(self._hostmap["%s"]): %s'
            debug(msg % (host, conn_total))

    def free_connection(self, conn):
        """
        Recycle a connection. Mark it as available for being reused.
        """
        if conn in self._used_cons:
            self._used_cons.remove(conn)
            self._free_conns.append(conn)

    def replace_connection(self, bad_conn, host, conn_factory):
        """
        Re-create a mal-functioning connection.

        :param bad_conn: The bad connection
        :param host: The host for the connection
        :param conn_factory: The factory function for new connection creation.
        """
        with self._lock:
            self.remove_connection(bad_conn, host)
            debug('keepalive: replacing bad connection with a new one')
            new_conn = conn_factory(host)
            conns = self._hostmap.setdefault(host, [])
            conns.append(new_conn)
            self._used_cons.append(new_conn)
            return new_conn

    def get_available_connection(self, host, conn_factory):
        """
        Return an available connection ready to be reused

        :param host: Host for the connection.
        :param conn_factory: Factory function for connection creation. Receives
                             <host> as parameter.
        """
        with self._lock:
            retry_count = self.GET_AVAILABLE_CONNECTION_RETRY_NUM

            while retry_count > 0:
                # First check if we can reuse an existing free connection from
                # the connection pool
                for conn in self._hostmap.setdefault(host, []):
                    try:
                        self._free_conns.remove(conn)
                    except ValueError:
                        continue
                    else:
                        self._used_cons.append(conn)
                        return conn

                # No? Well, if the connection pool is not full let's try to
                # create a new one.
                conn_total = self.get_connections_total(host)
                if conn_total < self._host_pool_size:
                    msg = 'keepalive: added one connection,'\
                          'len(self._hostmap["%s"]): %s'
                    debug(msg % (host, conn_total + 1))
                    conn = conn_factory(host)
                    self._used_cons.append(conn)
                    self._hostmap[host].append(conn)
                    return conn

                else:
                    # Well, the connection pool for this host is full, this
                    # means that many threads are sending request to the host
                    # and using the connections. This is not bad, just shows
                    # that w3af is keeping the connections busy
                    #
                    # Another reason for this situation is that the connections
                    # are *really* slow => taking many seconds to retrieve the
                    # HTTP response => not freeing often
                    #
                    # We should wait a little and try again
                    retry_count -= 1
                    time.sleep(self.GET_AVAILABLE_CONNECTION_RETRY_SECS)

            msg = 'HTTP connection pool (keepalive) waited too long (%s sec)' \
                  ' for a free connection, giving up. This usually occurs' \
                  ' when w3af is scanning using a slow connection, the remote' \
                  ' server is slow (or applying QoS to IP addresses flagged' \
                  ' as attackers).'
            seconds = (self.GET_AVAILABLE_CONNECTION_RETRY_NUM *
                       self.GET_AVAILABLE_CONNECTION_RETRY_SECS)
            raise ConnectionPoolException(msg % seconds)

    def get_all(self, host=None):
        """
        If <host> is passed return a list containing the created connections
        for that host. Otherwise return a dict with 'host: str' and
        'conns: list' as items.

        :param host: Host
        """
        if host:
            return list(self._hostmap.get(host, []))
        else:
            return dict(self._hostmap)

    def get_connections_total(self, host=None):
        """
        If <host> is None return the grand total of created connections;
        otherwise return the total of created conns. for <host>.
        """
        if host not in self._hostmap:
            return 0

        values = self._hostmap.values() if (host is None) \
            else [self._hostmap[host]]
        return reduce(operator.add, map(len, values or [[]]))


class KeepAliveHandler(object):
    
    def __init__(self):
        # Create the connection pool instance
        #
        # Note: In the initial code this connection manager was created at
        #       the module level and was shared between the HTTP and HTTPS
        #       keep alive handlers. This was buggy since at any point if
        #       a user requested http://host.tld and then https://host.tld
        #       a connection to the HTTP one was returned from the manager
        #       for the HTTPS request.
        #
        #       This change lets us still keep a "persistent" connection
        #       manager since our opener_settings and xurllib will only
        #       create one instance for the KeepAliveHandler and use that
        #       during the whole scan.
        self._cm = ConnectionManager()
        
        # Typically a urllib2.OpenerDirector instance. Set by the
        # urllib2 mechanism.
        self.parent = None
        self._pool_lock = threading.RLock()
        # Map hosts to a `collections.deque` of response status.
        self._hostresp = {}

    def get_open_connections(self):
        """
        Return a list of connected hosts and the number of connections
        to each.  [('foo.com:80', 2), ('bar.org', 1)]
        """
        return [(host, len(li)) for (host, li) in self._cm.get_all().items()]

    def close_connection(self, host):
        """
        Close connection(s) to <host>
        host is the host:port spec, as in 'www.cnn.com:8080' as passed in.
        no error occurs if there is no connection to that host.
        """
        for conn in self._cm.get_all(host):
            self._cm.remove_connection(conn, host)

    def close_all(self):
        """
        Close all open connections
        """
        for conns in self._cm.get_all().values():
            for conn in conns:
                self._cm.remove_connection(conn)

    def _request_closed(self, connection):
        """
        Tells us that this request is now closed and that the
        connection is ready for another request
        """
        self._cm.free_connection(connection)

    def _remove_connection(self, host, conn):
        self._cm.remove_connection(conn, host)

    def do_open(self, req):
        """
        Called by handler's url_open method.
        """
        host = req.get_host()
        if not host:
            raise urllib2.URLError('no host given')

        conn_factory = self._get_connection

        try:
            conn = self._cm.get_available_connection(host, conn_factory)
        except ConnectionPoolException:
            # When `self._cm.get_available_connection(host, conn_factory)` does
            # not return a conn, it will raise this exception. So we either get
            # here and `raise`, or we have a connection and something else
            # failed and we get to the other error handlers.
            raise

        try:
            if conn.is_fresh:
                # First of all, call the request method. This is needed for
                # HTTPS Proxy
                if isinstance(conn, ProxyHTTPConnection):
                    conn.proxy_setup(req.get_full_url())

                conn.is_fresh = False
                start = time.time()
                self._start_transaction(conn, req)
                resp = conn.getresponse()
            else:
                # We'll try to use a previously created connection
                start = time.time()
                resp = self._reuse_connection(conn, req, host)
                # If the resp is None it means that connection is bad. It was
                # possibly closed by the server. Replace it with a new one.
                if resp is None:
                    conn.close()
                    conn = self._cm.replace_connection(conn, host,
                                                       conn_factory)
                    # First of all, call the request method. This is needed for
                    # HTTPS Proxy
                    if isinstance(conn, ProxyHTTPConnection):
                        conn.proxy_setup(req.get_full_url())

                    # Try again with the fresh one
                    conn.is_fresh = False
                    start = time.time()
                    self._start_transaction(conn, req)
                    resp = conn.getresponse()

        except socket.timeout:
            # We better discard this connection
            self._cm.remove_connection(conn, host)
            raise URLTimeoutError()

        except (socket.error, httplib.HTTPException, OpenSSL.SSL.SysCallError):
            # We better discard this connection
            self._cm.remove_connection(conn, host)
            raise

        # This response seems to be fine
        # If not a persistent connection, don't try to reuse it
        if resp.will_close:
            self._cm.remove_connection(conn, host)

        resp._handler = self
        resp._host = host
        resp._url = req.get_full_url()
        resp._connection = conn
        resp.code = resp.status
        resp.headers = resp.msg
        resp.msg = resp.reason

        try:
            resp.read()
        except AttributeError:
            # The rare case of: 'NoneType' object has no attribute 'recv', we
            # read the response here because we're closer to the error and can
            # better understand it.
            #
            # https://github.com/andresriancho/w3af/issues/2074
            self._cm.remove_connection(conn, host)
            raise HTTPRequestException('The HTTP connection died')

        # We measure time here because it's the best place we know of
        elapsed = time.time() - start
        resp.set_wait_time(elapsed)

        debug("HTTP response: %s, %s" % (resp.status, resp.reason))
        return resp

    def _reuse_connection(self, conn, req, host):
        """
        Start the transaction with a re-used connection
        return a response object (r) upon success or None on failure.
        This DOES not close or remove bad connections in cases where
        it returns.  However, if an unexpected exception occurs, it
        will close and remove the connection before re-raising.
        """
        try:
            self._start_transaction(conn, req)
            r = conn.getresponse()
            # note: just because we got something back doesn't mean it
            # worked.  We'll check the version below, too.
        except (socket.error, httplib.HTTPException):
            r = None
        except Exception, e:
            # adding this block just in case we've missed something we will
            # still raise the exception, but lets try and close the connection
            # and remove it first.  We previously got into a nasty loop where
            # an exception was uncaught, and so the connection stayed open.
            # On the next try, the same exception was raised, etc. The tradeoff
            # is that it's now possible this call will raise a DIFFERENT
            # exception
            msg = 'unexpected exception "%s" - closing connection to %s (%d)'
            error(msg % (e, host, id(conn)))

            self._cm.remove_connection(conn, host)
            raise

        if r is None or r.version == 9:
            # httplib falls back to assuming HTTP 0.9 if it gets a
            # bad header back.  This is most likely to happen if
            # the socket has been closed by the server since we
            # last used the connection.
            debug("failed to re-use connection to %s (%d)" % (host, id(conn)))
            r = None
        else:
            debug("re-using connection to %s (%d)" % (host, id(conn)))
            r._multiread = None

        return r

    def _start_transaction(self, conn, req):
        """
        The real workhorse.
        """
        try:
            data = req.get_data()
            if data is not None:
                data = str(data)
                conn.putrequest(req.get_method(), req.get_selector(),
                                skip_host=1, skip_accept_encoding=1)

                if not req.has_header('Content-type'):
                    conn.putheader('Content-type',
                                   'application/x-www-form-urlencoded')

                if not req.has_header('Content-length'):
                    conn.putheader('Content-length', '%d' % len(data))
            else:
                conn.putrequest(req.get_method(), req.get_selector(),
                                skip_host=1, skip_accept_encoding=1)
        except (socket.error, httplib.HTTPException):
            raise
        else:
            # Add headers
            header_dict = dict(self.parent.addheaders)
            header_dict.update(req.headers)
            header_dict.update(req.unredirected_hdrs)

            for k, v in header_dict.iteritems():
                conn.putheader(to_utf8_raw(k),
                               to_utf8_raw(v))
            conn.endheaders()

            if data is not None:
                conn.send(data)

    def _get_connection(self, host):
        """
        "Abstract" method.
        """
        raise NotImplementedError()


class HTTPHandler(KeepAliveHandler, urllib2.HTTPHandler):
    def __init__(self):
        KeepAliveHandler.__init__(self)

    def http_open(self, req):
        return self.do_open(req)

    def _get_connection(self, host):
        return HTTPConnection(host)


class HTTPSHandler(KeepAliveHandler, urllib2.HTTPSHandler):
    def __init__(self, proxy):
        KeepAliveHandler.__init__(self)
        self._proxy = proxy
        try:
            host, port = self._proxy.split(':')
        except:
            msg = 'The proxy you are specifying (%s) is invalid! The expected'\
                  ' format is <ip_address>:<port> is expected.'
            raise BaseFrameworkException(msg % proxy)
        else:
            if not host or not port:
                self._proxy = None

    def https_open(self, req):
        return self.do_open(req)

    def _get_connection(self, host):
        if self._proxy:
            proxy_host, port = self._proxy.split(':')
            return ProxyHTTPSConnection(proxy_host, port)
        else:
            return HTTPSConnection(host)


