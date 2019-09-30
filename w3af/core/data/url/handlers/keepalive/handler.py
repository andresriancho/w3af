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
import time
import socket
import urllib2
import httplib
import OpenSSL
import threading

from email.base64mime import header_encode
from httplib import _is_legal_header_name, _is_illegal_header_value

from .utils import debug, error, to_utf8_raw
from .connection_manager import ConnectionManager
from .connections import (ProxyHTTPConnection, ProxyHTTPSConnection,
                          HTTPConnection, HTTPSConnection)
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              HTTPRequestException,
                                              ConnectionPoolException)


DEFAULT_CONTENT_TYPE = 'application/x-www-form-urlencoded'


class URLTimeoutError(urllib2.URLError):
    """
    Our own URLError timeout exception. Basically a wrapper for socket.timeout.
    """
    def __init__(self):
        urllib2.URLError.__init__(self, (408, 'timeout'))

    def __str__(self):
        default_timeout = socket.getdefaulttimeout()
        if default_timeout is not None:
            return 'HTTP timeout error after %s seconds' % default_timeout
        else:
            return 'HTTP timeout error'


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

    def close_connection(self, host):
        """
        Close connection(s) to <host>
        host is the host:port spec, as in 'www.cnn.com:8080' as passed in.
        no error occurs if there is no connection to that host.
        """
        for conn in self._cm.get_all(host):
            self._cm.remove_connection(conn, reason='close connection')

    def close_all(self):
        """
        Close all open connections
        """
        debug('Closing all connections')

        for conn in self._cm.get_all():
            self._cm.remove_connection(conn, reason='close all connections')

    def _request_closed(self, connection):
        """
        This request is now closed and that the connection is ready for another
        request
        """
        debug('Add %s to free-to-use connection list' % connection)
        self._cm.free_connection(connection)

    def _remove_connection(self, conn):
        self._cm.remove_connection(conn, reason='remove connection')

    def do_open(self, req):
        """
        Called by handler's url_open method.
        """
        host = req.get_host()
        if not host:
            raise urllib2.URLError('no host given')

        conn_factory = self.get_connection

        try:
            conn = self._cm.get_available_connection(req, conn_factory)
        except ConnectionPoolException:
            # When `self._cm.get_available_connection(host, conn_factory)` does
            # not return a conn, it will raise this exception. So we either get
            # here and `raise`, or we have a connection and something else
            # failed and we get to the other error handlers.
            raise

        try:
            if conn.is_fresh:
                resp, start = self._get_response(conn, req)
            else:
                # We'll try to use a previously created connection
                start = time.time()
                resp = self._reuse_connection(conn, req, host)

                # If the resp is None it means that connection is bad. It was
                # possibly closed by the server. Replace it with a new one.
                if resp is None:
                    conn = self._cm.replace_connection(conn, req, conn_factory)
                    resp, start = self._get_response(conn, req)

        except socket.timeout:
            # We better discard this connection
            self._cm.remove_connection(conn, reason='socket timeout')
            raise URLTimeoutError()

        except OpenSSL.SSL.ZeroReturnError:
            # According to the pyOpenSSL docs ZeroReturnError means that the
            # SSL connection has been closed cleanly
            self._cm.remove_connection(conn, reason='ZeroReturnError')
            raise

        except OpenSSL.SSL.SysCallError:
            # We better discard this connection
            self._cm.remove_connection(conn, reason='OpenSSL SysCallError')
            raise

        except OpenSSL.SSL.Error:
            #
            # OpenSSL.SSL.Error: [('SSL routines',
            #                      'ssl3_get_record',
            #                      'decryption failed or bad record mac')]
            #
            # Or something similar.
            #
            # Note that OpenSSL.SSL.Error is the base class for all the
            # OpenSSL exceptions, so we're catching quite a lot of things here
            # and the except order matters.
            #
            self._cm.remove_connection(conn, reason='OpenSSL.SSL.Error')
            raise

        except (socket.error, httplib.HTTPException):
            # We better discard this connection
            self._cm.remove_connection(conn, reason='socket error')
            raise

        except Exception, e:
            # We better discard this connection, we don't even know what happen!
            reason = 'unexpected exception "%s"' % e
            self._cm.remove_connection(conn, reason=reason)
            raise

        # How many requests were sent with this connection?
        conn.inc_req_count()

        # This response seems to be fine
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
            self._cm.remove_connection(conn, reason='http connection died')
            raise HTTPRequestException('The HTTP connection died')
        except Exception, e:
            # We better discard this connection, we don't even know what happen!
            reason = 'unexpected exception while reading "%s"' % e
            self._cm.remove_connection(conn, reason=reason)
            raise

        # If not a persistent connection, or the user specified that he wanted
        # a new connection for this specific request, don't try to reuse it
        if resp.will_close:
            self._cm.remove_connection(conn, reason='will close')
        elif req.new_connection:
            self._cm.remove_connection(conn, reason='new connection')

        # We measure time here because it's the best place we know of
        elapsed = time.time() - start
        resp.set_wait_time(elapsed)

        msg = "HTTP response: %s - %s - %s with %s in %s seconds"
        args = (req.get_selector(), resp.status, resp.reason, conn, elapsed)
        debug(msg % args)

        return resp

    def _get_response(self, conn, request):
        # First of all, call the request method. This is needed for
        # HTTPS Proxy
        if isinstance(conn, ProxyHTTPConnection):
            conn.proxy_setup(request.get_full_url())

        conn.is_fresh = False
        start = time.time()
        self._start_transaction(conn, request)
        resp = conn.getresponse()

        return resp, start

    def _reuse_connection(self, conn, req, host):
        """
        Start the transaction with a re-used connection
        return a response object (r) upon success or None on failure.
        This DOES not close or remove bad connections in cases where
        it returns.  However, if an unexpected exception occurs, it
        will close and remove the connection before re-raising.
        """
        reason = None

        try:
            self._start_transaction(conn, req)
            resp = conn.getresponse()
            # note: just because we got something back doesn't mean it
            # worked.  We'll check the version below, too.
        except (socket.error, httplib.HTTPException), e:
            self._cm.remove_connection(conn, reason='socket error')
            resp = None
            reason = e
        except OpenSSL.SSL.ZeroReturnError, e:
            # According to the pyOpenSSL docs ZeroReturnError means that the
            # SSL connection has been closed cleanly
            self._cm.remove_connection(conn, reason='ZeroReturnError')
            resp = None
            reason = e
        except OpenSSL.SSL.SysCallError, e:
            # Not sure why we're getting this exception when trying to reuse a
            # connection (but not when doing the initial request). So we just
            # ignore the exception and go on.
            #
            # A new connection will be created and the scan should continue without
            # problems
            self._cm.remove_connection(conn, reason='OpenSSL.SSL.SysCallError')
            resp = None
            reason = e
        except Exception, e:
            # adding this block just in case we've missed something we will
            # still raise the exception, but lets try and close the connection
            # and remove it first.  We previously got into a nasty loop where
            # an exception was uncaught, and so the connection stayed open.
            # On the next try, the same exception was raised, etc. The tradeoff
            # is that it's now possible this call will raise a DIFFERENT
            # exception
            msg = 'Unexpected exception "%s" - closing %s to %s)'
            error(msg % (e, conn, host))

            self._cm.remove_connection(conn, reason='unexpected %s' % e)
            raise

        if resp is None or resp.version == 9:
            # httplib falls back to assuming HTTP 0.9 if it gets a
            # bad header back.  This is most likely to happen if
            # the socket has been closed by the server since we
            # last used the connection.
            msg = 'Failed to re-use %s to %s due to exception "%s"'
            args = (conn, host, reason)
            debug(msg % args)

            resp = None
        else:
            debug('Re-using %s to %s' % (conn, host))
            resp._multiread = None

        return resp

    def _update_socket_timeout(self, conn, request):
        """
        If the HttpConnection instance has an active socket connection,
        then we update the timeout.

        :param conn: The HTTPConnection
        :param request: The new request to be sent via the connection
        :return: None, we just update conn
        """
        if conn.sock is None:
            return

        if isinstance(conn, HTTPConnection):
            conn.sock.settimeout(request.get_timeout())

    def _start_transaction(self, conn, req):
        """
        The real workhorse.
        """
        self._update_socket_timeout(conn, req)

        conn.putrequest(req.get_method(),
                        req.get_selector(),
                        skip_host=1,
                        skip_accept_encoding=1)

        # We're always sending HTTP/1.1, which makes connection keep alive a
        # default, BUT since the browsers (Chrome at least) send this header
        # in their HTTP/1.1 requests we're going to do the same just to make
        # sure we behave like a browser
        if not req.has_header('Connection'):
            conn.putheader('Connection', 'keep-alive')

        data = req.get_data()
        if data is not None:
            data = str(data)

            if not req.has_header('Content-type'):
                conn.putheader('Content-type', DEFAULT_CONTENT_TYPE)

            if not req.has_header('Content-length'):
                conn.putheader('Content-length', '%d' % len(data))

        # Add headers
        header_dict = dict(self.parent.addheaders)
        header_dict.update(req.headers)
        header_dict.update(req.unredirected_hdrs)

        for k, v in header_dict.iteritems():
            #
            # Handle case where the key or value is None (strange but could happen)
            #
            if k is None:
                continue

            if v is None:
                v = ''

            #
            # Encode the key and value as UTF-8 and try to send them to the wire
            #
            k = to_utf8_raw(k)
            v = to_utf8_raw(v)

            try:
                conn.putheader(k, v)
            except ValueError:
                #
                # The httplib adds some restrictions to the characters which can
                # be sent in header names and values (see putheader function
                # definition).
                #
                # Sending non-ascii characters in HTTP header values is difficult,
                # since servers usually ignore the encoding. From stackoverflow:
                #
                # Historically, HTTP has allowed field content with text in the
                # ISO-8859-1 charset [ISO-8859-1], supporting other charsets only
                # through use of [RFC2047] encoding. In practice, most HTTP header
                # field values use only a subset of the US-ASCII charset [USASCII].
                # Newly defined header fields SHOULD limit their field values to
                # US-ASCII octets. A recipient SHOULD treat other octets in field
                # content (obs-text) as opaque data.
                #
                # TL;DR: we use RFC2047 encoding here, knowing that it will only
                #        work in 1% of the remote servers, but it is our best bet
                #
                if not _is_legal_header_name(k):
                    k = header_encode(k, charset='utf-8', keep_eols=True)

                if _is_illegal_header_value(v):
                    v = header_encode(v, charset='utf-8', keep_eols=True)

                conn.putheader(k, v)

        conn.endheaders()

        if data is not None:
            conn.send(data)

    def get_connection(self, host):
        """
        "Abstract" method which needs to be implemented in the sub-classes
        """
        raise NotImplementedError()


class HTTPHandler(KeepAliveHandler, urllib2.HTTPHandler):
    def __init__(self):
        KeepAliveHandler.__init__(self)
        urllib2.HTTPHandler.__init__(self, debuglevel=0)

    def http_open(self, req):
        return self.do_open(req)

    def get_connection(self, request):
        return HTTPConnection(request.get_host(), timeout=request.get_timeout())


class HTTPSHandler(KeepAliveHandler, urllib2.HTTPSHandler):
    def __init__(self, proxy):
        KeepAliveHandler.__init__(self)
        urllib2.HTTPSHandler.__init__(self, debuglevel=0)

        self._proxy = proxy
        try:
            host, port = self._proxy.split(':')
        except:
            msg = ('The proxy you are specifying (%s) is invalid! The expected'
                   ' format is <ip_address>:<port> is expected.')
            raise BaseFrameworkException(msg % proxy)
        else:
            if not host or not port:
                self._proxy = None

    def https_open(self, req):
        return self.do_open(req)

    def get_connection(self, request):
        use_proxy = getattr(request, 'use_proxy', False)
        if self._proxy and use_proxy:
            proxy_host, proxy_port = self._proxy.split(':')
            return ProxyHTTPSConnection(proxy_host,
                                        proxy_port,
                                        timeout=request.get_timeout())
        else:
            return HTTPSConnection(request.get_host(),
                                   timeout=request.get_timeout())



