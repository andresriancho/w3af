#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the 
#     Free Software Foundation, Inc., 
#     59 Temple Place, Suite 330, 
#     Boston, MA  02111-1307  USA

# This file is part of urlgrabber, a high-level cross-protocol url-grabber
# Copyright 2002-2004 Michael D. Stenner, Ryan Tomayko

# This file was modified (considerably) to be integrated with w3af. Some modifications are:
#   - Added the size limit for responses
#   - Raising w3afExceptions in some places
#   - Modified the HTTPResponse object in order to be able to perform multiple reads, and
#     added a hack for the HEAD method.

"""An HTTP handler for urllib2 that supports HTTP 1.1 and keepalive.

>> import urllib2
>> from keepalive import HTTPHandler
>> keepalive_handler = HTTPHandler()
>> opener = urllib2.build_opener(keepalive_handler)
>> urllib2.install_opener(opener)
>> 
>> fo = urllib2.urlopen('http://www.python.org')

If a connection to a given host is requested, and all of the existing
connections are still in use, another connection will be opened.  If
the handler tries to use an existing connection but it fails in some
way, it will be closed and removed from the pool.

To remove the handler, simply re-run build_opener with no arguments, and
install that opener.

You can explicitly close connections by using the close_connection()
method of the returned file-like object (described below) or you can
use the handler methods:

  close_connection(host)
  close_all()
  get_open_connections()

NOTE: using the close_connection and close_all methods of the handler
should be done with care when using multiple threads.
  * there is nothing that prevents another thread from creating new
    connections immediately after connections are closed
  * no checks are done to prevent in-use connections from being closed

>> keepalive_handler.close_all()

EXTRA ATTRIBUTES AND METHODS

  Upon a status of 200, the object returned has a few additional
  attributes and methods, which should not be used if you want to
  remain consistent with the normal urllib2-returned objects:

    close_connection()  -  close the connection to the host
    readlines()      -  you know, readlines()
    status            -  the return status (ie 404)
    reason            -  english translation of status (ie 'File not found')

  If you want the best of both worlds, use this inside an
  AttributeError-catching try:

    >> try:
    ...     status = fo.status
    ... except AttributeError:
    ...     status = None

  Unfortunately, these are ONLY there if status == 200, so it's not
  easy to distinguish between non-200 responses.  The reason is that
  urllib2 tries to do clever things with error codes 301, 302, 401,
  and 407, and it wraps the object upon return.

  For python versions earlier than 2.4, you can avoid this fancy error
  handling by setting the module-level global HANDLE_ERRORS to zero.
  You see, prior to 2.4, it's the HTTP Handler's job to determine what
  to handle specially, and what to just pass up.  HANDLE_ERRORS == 0
  means "pass everything up".  In python 2.4, however, this job no
  longer belongs to the HTTP Handler and is now done by a NEW handler,
  HTTPErrorProcessor.  Here's the bottom line:

    python version < 2.4
        HANDLE_ERRORS == 1  (default) pass up 200, treat the rest as
                            errors
        HANDLE_ERRORS == 0  pass everything up, error processing is
                            left to the calling code
    python version >= 2.4
        HANDLE_ERRORS == 1  pass up 200, treat the rest as errors
        HANDLE_ERRORS == 0  (default) pass everything up, let the
                            other handlers (specifically,
                            HTTPErrorProcessor) decide what to do

  In practice, setting the variable either way makes little difference
  in python 2.4, so for the most consistent behavior across versions,
  you probably just want to use the defaults, which will give you
  exceptions on errors.

"""

# $Id: keepalive.py,v 1.16 2006/09/22 00:58:05 mstenner Exp $

from __future__ import with_statement
import urllib2
import httplib
import operator
import socket
import threading
import urllib
import sys
import time

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException, \
    w3afMustStopByKnownReasonExc
from core.controllers.misc.datastructs import deque
import core.data.kb.config as cf
from core.data.constants.httpConstants import NO_CONTENT

HANDLE_ERRORS = 1 if sys.version_info < (2, 4) else 0
DEBUG = None

# Global connection timeout. In seconds.
TIMEOUT = 25
# Max connections allowed per host.
MAXCONNECTIONS = 50
# If found this number of timeouts in-a-row per target host then we may either:
#    1) Shrink the pool size (we might be stressing the remote host) and retry;
#        or:
#    2) Give up and make w3af stop sending requests for that host.
# This number should not be greater than (MAXCONNECTIONS / 2)
IN_A_ROW_TIMEOUTS = 15
# Constants for responses statuses
RESP_OK = 0
RESP_TIMEOUT = 1
RESP_BAD = 2

class URLTimeoutError(urllib2.URLError):
    '''
    Our own URLError timeout exception. Basically a wrapper for socket.timeout.
    '''
    def __init__(self):
        urllib2.URLError.__init__(self, (408, 'timeout'))

    def __str__(self):
        return '<urlopen error timeout>'

def closeonerror(read_meth):
    '''
    Decorator function. When calling decorated `read_meth` if an error occurs
    we'll proceed to invoke `inst`'s close() method.
    '''
    def new_read_meth(inst):
        try:
            return read_meth(inst)
        except httplib.HTTPException:
            inst.close()
            raise
    return new_read_meth

class HTTPResponse(httplib.HTTPResponse):
    # we need to subclass HTTPResponse in order to
    # 1) add readline() and readlines() methods
    # 2) add close_connection() methods
    # 3) add info() and geturl() methods

    # in order to add readline(), read must be modified to deal with a
    # buffer.  example: readline must read a buffer and then spit back
    # one line at a time.  The only real alternative is to read one
    # BYTE at a time (ick).  Once something has been read, it can't be
    # put back (ok, maybe it can, but that's even uglier than this),
    # so if you THEN do a normal read, you must first take stuff from
    # the buffer.

    # the read method wraps the original to accomodate buffering,
    # although read() never adds to the buffer.
    # Both readline and readlines have been stolen with almost no
    # modification from socket.py


    def __init__(self, sock, debuglevel=0, strict=0, method=None):
        if method: # the httplib in python 2.3 uses the method arg
            httplib.HTTPResponse.__init__(self, sock, debuglevel, method)
        else: # 2.2 doesn't
            httplib.HTTPResponse.__init__(self, sock, debuglevel)
        self.fileno = sock.fileno
        self.code = None
        self._rbuf = ''
        self._rbufsize = 8096
        self._handler = None # inserted by the handler later
        self._host = None   # (same)
        self._url = None     # (same)
        self._connection = None # (same)
        self._method = method
        self._multiread = None

    def _raw_read(self, amt=None):
        '''
        This is the original read function from httplib with a minor 
        modification that allows me to check the size of the file being 
        fetched, and throw an exception in case it is too big.
        '''
        if self.fp is None:
            return ''

        if self.length > cf.cf.getData('maxFileSize'):
            self.status = NO_CONTENT
            self.reason = 'No Content'  # Reason-Phrase
            self.close()
            return ''

        if self.chunked:
            return self._read_chunked(amt)

        if amt is None:
            # unbounded read
            if self.length is None:
                s = self.fp.read()
            else:
                s = self._safe_read(self.length)
                self.length = 0
            self.close()        # we read everything
            return s

        if self.length is not None:
            if amt > self.length:
                # clip the read to the "end of response"
                amt = self.length

        # we do not use _safe_read() here because this may be a .will_close
        # connection, and the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        s = self.fp.read(amt)
        if self.length is not None:
            self.length -= len(s)

        return s

    def close(self):
        # First call parent's close()
        httplib.HTTPResponse.close(self)
        if self._handler:
            self._handler._request_closed(self._connection)

    def close_connection(self):
        self._handler._remove_connection(self._host, self._connection)
        self.close()

    def info(self):
        return self.headers

    def geturl(self):
        return self._url

    @closeonerror
    def read(self, amt=None):
        # w3af does always read all the content of the response...
        # and I also need to do multiple reads to this response...
        # BUGBUG: Is this OK? What if a HEAD method actually returns something?!
        if self._method == 'HEAD':
            # This indicates that we have read all that we needed from the socket
            # and that the socket can be reused!
            #
            # This like fixes the bug with title "GET is much faster than HEAD".
            #https://sourceforge.net/tracker2/?func=detail&aid=2202532&group_id=170274&atid=853652
            self.close()
            return ''

        if self._multiread is None:
            #read all
            self._multiread = self._raw_read()

        if not amt is None:
            L = len(self._rbuf)
            if amt > L:
                amt -= L
            else:
                s = self._rbuf[:amt]
                self._rbuf = self._rbuf[amt:]
                return s
        else:
            s = self._rbuf + self._multiread
            self._rbuf = ''
            return s

    def readline(self, limit=-1):
        data = ""
        i = self._rbuf.find('\n')
        while i < 0 and not (0 < limit <= len(self._rbuf)):
            new = self._raw_read(self._rbufsize)
            if not new: break
            i = new.find('\n')
            if i >= 0: i = i + len(self._rbuf)
            self._rbuf = self._rbuf + new
        if i < 0: i = len(self._rbuf)
        else: i = i + 1
        if 0 <= limit < len(self._rbuf): i = limit
        data, self._rbuf = self._rbuf[:i], self._rbuf[i:]
        return data

    @closeonerror
    def readlines(self, sizehint=0):
        total = 0
        list = []
        while 1:
            line = self.readline()
            if not line: break
            list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return list

    def setBody(self, data):
        '''
        This was added to make my life a lot simpler while implementing mangle
        plugins
        '''
        self._multiread = data


class ConnectionManager:
    '''
    The connection manager must be able to:
        * keep track of all existing HTTPConnections
        * kill the connections that we're not going to use anymore
        * Create/reuse connections when needed.
        * Control the size of the pool.
    '''

    def __init__(self):
        self._lock = threading.RLock()
        self._host_pool_size = MAXCONNECTIONS
        self._hostmap = {} # map hosts to a list of connections
        self._used_cons = [] # connections being used per host
        self._free_conns = [] # available connections

    def remove_connection(self, conn, host=None):
        '''
        Remove a connection, it was closed by the server.
        
        @param conn: Connection to remove
        @param host: The host for to the connection. If passed, the connection
        will be removed faster.
        '''
        with self._lock:

            if host:
                if host not in self._hostmap:
                    raise ValueError, 'Host "%s" not present in pool.' % host
                self._hostmap[host].remove(conn)

            else: # We don't know the host. Need to find it by looping
                for _host, conns in self._hostmap.items():
                    if conn in conns:
                        host = _host
                        conns.remove(conn)
                        break

            removed = False
            try:
                self._used_cons.remove(conn)
                removed = True
            except ValueError:
                try:
                    self._free_conns.remove(conn)
                    removed = True
                except ValueError:
                    pass
            if not removed:
                raise ValueError, "Connection obj <%s> not present in pool" % \
                conn

            conn_total = self.get_connections_total(host)
            msg = 'keepalive: removed one connection, len(self._hostmap' \
            '["%s"]): %s' % (host, conn_total)
            om.out.debug(msg)

            # No more conns for 'host', remove it from mapping
            if host and not conn_total:
                del self._hostmap[host]

    def free_connection(self, conn):
        '''
        Recycle a connection. Mark it as available for being reused.
        '''
        if conn in self._used_cons:
            self._used_cons.remove(conn)
            self._free_conns.append(conn)

    def replace_connection(self, bad_conn, host, conn_factory):
        '''
        Re-create a mal-functioning connection.
        
        @param bad_conn: The bad connection
        @param host: The host for the connection
        @param conn_factory: The factory function for new connection creation.
        '''
        with self._lock:
            self.remove_connection(bad_conn, host)
            msg = 'keepalive: replacing bad connection with a new one'
            om.out.debug(msg)
            new_conn = conn_factory(host)
            conns = self._hostmap.setdefault(host, [])
            conns.append(new_conn)
            self._used_cons.append(new_conn)
            return new_conn

    def get_available_connection(self, host, conn_factory):
        '''
        Return an available connection ready to be reused
        
        @param host: Host for the connection.
        @param conn_factory: Factory function for connection creation. Receives
            <host> as parameter.
        '''
        with self._lock:
            retry_count = 10

            while retry_count > 0:
                ret_conn = None

                # First check if we can reuse an existing free conn.
                for conn in self._hostmap.setdefault(host, []):
                    try:
                        self._free_conns.remove(conn)
                    except ValueError:
                        continue
                    else:
                        self._used_cons.append(conn)
                        ret_conn = conn
                        break

                # No?... well, let's try to create a new one.
                conn_total = self.get_connections_total(host)
                if not ret_conn and conn_total < self._host_pool_size:
                    msg = 'keepalive: added one connection, len(self._hostmap'\
                    '["%s"]): %s' % (host, conn_total + 1)
                    om.out.debug(msg)
                    ret_conn = conn_factory(host)
                    self._used_cons.append(ret_conn)
                    self._hostmap[host].append(ret_conn)

                if ret_conn is not None: # Good! We have one!
                    return ret_conn
                else: # Maybe we should wait a little and try again 8^)
                    retry_count -= 1
                    time.sleep(0.3)

            msg = 'keepalive: been waiting too long for a pool connection.' \
            ' I\'m giving up. Seems like the pool is full.'
            om.out.debug(msg)
            raise w3afException(msg)

    def resize_pool(self, new_size):
        '''
        Set a new pool size.
        '''
        pass


    def get_all(self, host=None):
        '''
        If <host> is passed return a list containing the created connections
        for that host. Otherwise return a dict with 'host: str' and 
        'conns: list' as items.
        
        @param host: Host
        '''
        if host:
            return list(self._hostmap.get(host, []))
        else:
            return dict(self._hostmap)

    def get_connections_total(self, host=None):
        '''
        If <host> is None return the grand total of created connections; 
        otherwise return the total of created conns. for <host>.
        '''
        values = self._hostmap.values() if (host is None) \
                                            else [self._hostmap[host]]
        return reduce(operator.add, map(len, values or [[]]))

# Create the pool instance to be used. Intended to be shared by handlers.
# See our HTTPHandler and HTTPSHandler class definitions below.
connMgr = ConnectionManager()


class KeepAliveHandler:

    _cm = connMgr

    def __init__(self):
        # Typically a urllib2.OpenerDirector instance. Set by the
        # urllib2 mechanism.
        self.parent = None
        self._pool_lock = threading.RLock()
        # Map hosts to a `collections.deque` of response status.
        self._hostresp = {}
        # Current number of 'in-a-row-timeouts'. It may vary depending on the
        # current size of the pool.
        self._curr_check_failures = IN_A_ROW_TIMEOUTS
        # Tail list filter factory function
        self._get_tail_filter = lambda: deque(maxlen=self._curr_check_failures)


    def get_open_connections(self):
        '''
        Return a list of connected hosts and the number of connections
        to each.  [('foo.com:80', 2), ('bar.org', 1)]
        '''
        return [(host, len(li)) for (host, li) in self._cm.get_all().items()]

    def close_connection(self, host):
        '''
        Close connection(s) to <host>
        host is the host:port spec, as in 'www.cnn.com:8080' as passed in.
        no error occurs if there is no connection to that host.
        '''
        for conn in self._cm.get_all(host):
            self._cm.remove_connection(conn, host)
            conn.close()

    def close_all(self):
        '''
        Close all open connections
        '''
        for conns in self._cm.get_all().values():
            for conn in conns:
                self._cm.remove_connection(conn)
                conn.close()

    def _request_closed(self, connection):
        '''
        Tells us that this request is now closed and that the
        connection is ready for another request
        '''
        self._cm.free_connection(connection)

    def _remove_connection(self, host, conn):
        self._cm.remove_connection(conn, host)
        conn.close()

    def do_open(self, req):
        '''
        Called by handler's url_open method.
        '''
        host = req.get_host()
        if not host:
            raise urllib2.URLError('no host given')

        try:
            resp_statuses = self._hostresp.setdefault(host,
                                                      self._get_tail_filter())
            # Check if all our last 'resp_statuses' were timeouts and raise
            # a w3afMustStopException if this is the case.
            if len(resp_statuses) == self._curr_check_failures and \
                all(st == RESP_TIMEOUT for st in resp_statuses):
                msg = ('w3af found too much consecutive timeouts. The remote '
                'webserver seems to be unresponsive; please verify manually.')
                reason = 'Timeout while trying to reach target.'
                raise w3afMustStopByKnownReasonExc(msg, reason=reason)

            conn_factory = self._get_connection
            conn = self._cm.get_available_connection(host, conn_factory)

            if conn.is_fresh:
                # First of all, call the request method. This is needed for
                # HTTPS Proxy
                if isinstance(conn, ProxyHTTPConnection):
                    conn.proxy_setup(req.get_full_url())

                conn.is_fresh = False
                self._start_transaction(conn, req)
                resp = conn.getresponse()
            else:
                # We'll try to use a previously created connection
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
                    self._start_transaction(conn, req)
                    resp = conn.getresponse()

        except (socket.error, httplib.HTTPException), err:
            # We better discard this connection
            self._cm.remove_connection(conn, host)
            if isinstance(err, socket.timeout):
                resp_statuses.append(RESP_TIMEOUT)
                _err = URLTimeoutError()
            else:
                resp_statuses.append(RESP_BAD)
                if isinstance(err, httplib.HTTPException):
                    err = repr(err)
                _err = urllib2.URLError(err)
            raise _err

        # This response seems to be fine
        resp_statuses.append(RESP_OK)

        # If not a persistent connection, don't try to reuse it
        if resp.will_close:
            self._cm.remove_connection(conn, host)

        if DEBUG:
            DEBUG.info("STATUS: %s, %s", resp.status, resp.reason)
        resp._handler = self
        resp._host = host
        resp._url = req.get_full_url()
        resp._connection = conn
        resp.code = resp.status
        resp.headers = resp.msg
        resp.msg = resp.reason
        return resp


    def _reuse_connection(self, conn, req, host):
        '''
        Start the transaction with a re-used connection
        return a response object (r) upon success or None on failure.
        This DOES not close or remove bad connections in cases where
        it returns.  However, if an unexpected exception occurs, it
        will close and remove the connection before re-raising.
        '''
        try:
            self._start_transaction(conn, req)
            r = conn.getresponse()
            # note: just because we got something back doesn't mean it
            # worked.  We'll check the version below, too.
        except (socket.error, httplib.HTTPException):
            r = None
        except:
            # adding this block just in case we've missed something we will
            # still raise the exception, but lets try and close the connection
            # and remove it first.  We previously got into a nasty loop where
            # an exception was uncaught, and so the connection stayed open.
            # On the next try, the same exception was raised, etc. The tradeoff
            # is that it's now possible this call will raise a DIFFERENT
            # exception
            if DEBUG:
                DEBUG.error("unexpected exception - closing connection to %s" \
                            " (%d)", host, id(conn))
            self._cm.remove_connection(conn, host)
            conn.close()
            raise

        if r is None or r.version == 9:
            # httplib falls back to assuming HTTP 0.9 if it gets a
            # bad header back.  This is most likely to happen if
            # the socket has been closed by the server since we
            # last used the connection.
            if DEBUG:
                DEBUG.info("failed to re-use connection to %s (%d)", host,
                           id(conn))
            r = None
        else:
            if DEBUG:
                DEBUG.info("re-using connection to %s (%d)", host, id(conn))
            r._multiread = None

        return r

    def _start_transaction(self, conn, req):
        '''
        The real workhorse.
        '''
        try:
            if req.has_data():
                data = req.get_data()
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
        except httplib.ImproperConnectionState:
            raise
        except (socket.error, httplib.HTTPException), err:
            raise urllib2.URLError(err)

        # Add headers.
        headerDict = dict(self.parent.addheaders)
        headerDict.update(req.headers)
        headerDict.update(req.unredirected_hdrs)

        for k, v in headerDict.iteritems():
            conn.putheader(k, v)
        conn.endheaders()

        if req.has_data():
            conn.send(data)

    def _get_connection(self, host):
        '''
        "Abstract" method.
        '''
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
        host = port = ''
        try:
            host, port = self._proxy.split(':')
        except:
            msg = 'The proxy you are specifying is invalid! ('
            msg += self._proxy + '), IP:Port is expected.'
            raise w3afException(msg)

        if not host or not port:
            self._proxy = None

    def https_open(self, req):
        return self.do_open(req)

    def _get_connection(self, host):
        if self._proxy:
            proxyHost, port = self._proxy.split(':')
            return ProxyHTTPSConnection(proxyHost, port)
        else:
            return HTTPSConnection(host)

class _HTTPConnection(httplib.HTTPConnection):

    def __init__(self, host, port=None, strict=None):
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.is_fresh = True


class ProxyHTTPConnection(_HTTPConnection):
    '''
    this class is used to provide HTTPS CONNECT support.
    '''
    _ports = {'http' : 80, 'https' : 443}

    def __init__(self, host, port=None, strict=None):
        _HTTPConnection.__init__(self, host, port, strict)

    def proxy_setup(self, url):
        #request is called before connect, so can interpret url and get
        #real host/port to be used to make CONNECT request to proxy
        proto, rest = urllib.splittype(url)
        if proto is None:
            raise ValueError, "unknown URL type: %s" % url
        #get host
        host, rest = urllib.splithost(rest)
        self._real_host = host

        #try to get port
        host, port = urllib.splitport(host)
        #if port is not defined try to get from proto
        if port is None:
            try:
                self._real_port = self._ports[proto]
            except KeyError:
                raise ValueError, "unknown protocol for: %s" % url
        else:
            self._real_port = int(port)

    def connect(self):
        httplib.HTTPConnection.connect(self)
        #send proxy CONNECT request
        self.send("CONNECT %s:%d HTTP/1.0\r\n\r\n" % (self._real_host,
                                                      self._real_port))
        #expect a HTTP/1.0 200 Connection established
        response = self.response_class(self.sock, strict=self.strict,
                                       method=self._method)
        (version, code, message) = response._read_status()
        #probably here we can handle auth requests...
        if code != 200:
            #proxy returned and error, abort connection, and raise exception
            self.close()
            raise socket.error, "Proxy connection failed: %d %s" % \
            (code, message.strip())
        #eat up header block from proxy....
        while True:
            #should not use directly fp probablu
            line = response.fp.readline()
            if line == '\r\n': break

class ProxyHTTPSConnection(ProxyHTTPConnection):
    '''
    this class is used to provide HTTPS CONNECT support.
    '''
    default_port = 443

    # Customized response class
    response_class = HTTPResponse

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None):
        ProxyHTTPConnection.__init__(self, host, port)
        self.key_file = key_file
        self.cert_file = cert_file

    def connect(self):
        ProxyHTTPConnection.connect(self)
        #make the sock ssl-aware
        ssl = socket.ssl(self.sock, self.key_file, self.cert_file)
        self.sock = httplib.FakeSocket(self.sock, ssl)

class HTTPConnection(_HTTPConnection):
    # use the modified response class
    response_class = HTTPResponse

    # TODO: In Python > 2.5 the timeout is a constructor parameter. The 
    # socket.setdefaulttimeout(TIMEOUT) call will no longer be needed.
    # CHANGE ME!!
    def __init__(self, host, port=None, strict=None):
        _HTTPConnection.__init__(self, host, port, strict)
        socket.setdefaulttimeout(TIMEOUT)

class HTTPSConnection(httplib.HTTPSConnection):
    response_class = HTTPResponse

    # TODO: In Python > 2.5 the timeout is a constructor parameter. The 
    # socket.setdefaulttimeout(TIMEOUT) call will no longer be needed.
    # CHANGE ME!!
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None):
        httplib.HTTPSConnection.__init__(self, host, port, key_file, cert_file,
                                        strict)
        socket.setdefaulttimeout(TIMEOUT)
        self.is_fresh = True
