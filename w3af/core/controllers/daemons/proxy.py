"""
proxy.py

Copyright 2006 Andres Riancho

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
import cStringIO
import traceback
import socket
import select
import httplib
import time
import os
import SocketServer

from OpenSSL import SSL
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException, ProxyException
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers


class w3afProxyHandler(BaseHTTPRequestHandler):

    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.

        I override this because I'm going to use ONE handler for all the
        methods (except CONNECT).
        """
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        
        # An error code has been sent, just exit
        if not self.parse_request():
            return

        # Now I perform my specific tasks...
        if self.command == 'QUIT':
            # Stop the server
            self.send_response(200)
            self.end_headers()
            self.server.stop = True
            om.out.debug('Handled QUIT request.')
        elif self.command == 'CONNECT':
            self.do_CONNECT()
        else:
            self.do_ALL()

    def _get_post_data(self):
        """
        :return: Post data preserving rfile
        """
        post_data = None
        if 'content-length' in self.headers.dict:
            cl = int(self.headers['content-length'])
            post_data = self.rfile.read(cl)
            # rfile is not seekable, so a little trick
            if not hasattr(self.rfile, 'reset'):
                rfile = cStringIO.StringIO(post_data)
                self.rfile = rfile
            self.rfile.reset()
        return post_data

    def _create_fuzzable_request(self):
        """
        Based on the attributes, return a fuzzable request object.

        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the post_data
            - self.path : Stores the URL that was requested by the browser
        """
        # See HTTPWrapperClass
        if hasattr(self.server, 'chainedHandler'):
            base_path = "https://" + self.server.chainedHandler.path
            path = base_path + self.path
        else:
            path = self.path

        fuzzable_request = FuzzableRequest(URL(path), self.command,
                                           Headers(self.headers.dict.items()))

        post_data = self._get_post_data()
        if post_data:
            fuzzable_request.set_data(post_data)

        return fuzzable_request

    def do_ALL(self):
        """
        This method handles EVERY request that was send by the browser.
        """
        try:
            # Send the request to the remote webserver
            # The request parameters such as the URL, the headers, etc. are
            # stored in "self". Note: This is the way that the HTTPServer and
            # the Handler work in python; this wasn't my choice.
            res = self._send_to_server()
        except Exception, e:
            self._send_error(e, trace=str(traceback.format_exc()))
        else:
            try:
                self._send_to_browser(res)
            except Exception, e:
                msg = 'Exception found while sending response to the browser.'\
                      ' Exception details: "%s".' % str(e)
                om.out.debug(msg)

    def _send_to_server(self, grep=False):
        """
        Send a request that arrived from the browser to the remote web server.

        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the post_data
            - self.path : Stores the URL that was requested by the browser
        """
        self.headers['Connection'] = 'close'

        path = self.path

        # See HTTPWrapperClass
        if hasattr(self.server, 'chainedHandler'):
            base_path = "https://" + self.server.chainedHandler.path
            path = base_path + path

        uri_instance = URL(path)

        #
        # Do the request to the remote server
        #
        post_data = None
        if 'content-length' in self.headers.dict:
            # most likely a POST request
            post_data = self._get_post_data()

        try:
            http_method = getattr(self._uri_opener, self.command)
            res = http_method(uri_instance, data=post_data,
                              headers=Headers(self.headers.items()),
                              grep=grep)
        except BaseFrameworkException, w:
            om.out.error('The proxy request failed, error: ' + str(w))
            raise w
        except Exception, e:
            raise e
        else:
            return res

    def _send_error(self, exceptionObj, trace=None):
        """
        Send an error to the browser.

        Important methods used here:
            - self.send_header : Sends a header to the browser
            - self.end_headers : Ends the headers section
            - self.wfile : A file like object that represents the body of the response
        """
        try:
            self.send_response(400)
            self.send_header('Connection', 'close')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # FIXME: Make this error look nicer
            self.wfile.write(
                'w3af proxy error: ' + str(exceptionObj) + '<br/><br/>')
            if trace:
                self.wfile.write('Traceback for this error: <br/><br/>' +
                                 trace.replace('\n', '<br/>'))

        except Exception, e:
            traceback.print_exc()
            msg = 'An error occurred in proxy._send_error(). Maybe the browser'\
                  ' closed the connection? Exception: %s.' % e
            om.out.debug(msg)

        self.wfile.close()

    def send_response(self, code, message=None):
        """Send the response header and log the response code.

        I'm overriding this method in order to avoid this:

            ***
            Also send two standard headers with the server
            software version and the current date.
            ***

        """
        self.log_request(code)
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s\r\n" %
                             (self.protocol_version, code, message))
            # print (self.protocol_version, code, message)
        #self.send_header('Server', self.version_string())
        #self.send_header('Date', self.date_time_string())

    def _send_to_browser(self, res):
        """
        Send a response that was sent by the remote web server to the browser

        Important methods used here:
            - self.send_header : Sends a header to the browser
            - self.end_headers : Ends the headers section
            - self.wfile : A file like object that represents the body
                of the response
        """
        send_header = self.send_header
        try:
            self.send_response(res.get_code())

            what_to_send = res.body
            if res.is_text_or_html():
                what_to_send = what_to_send.encode(res.charset, 'replace')

            # Work with the response's headers.
            # Overwrite 'content-length'
            send_header('content-length', str(len(what_to_send)))
            send_header('connection', 'close')

            for header, value in res.get_lower_case_headers().items():
                # Ignore these headers:
                #   - 'content-length', as it has been overwritten before
                #   - 'transfer-encoding', when 'chunked' as the
                #     response has already been read completely.
                if (header == 'content-length') or \
                   (header == 'connection') or \
                   (header == 'transfer-encoding' and value.lower() == 'chunked') or \
                   (value.lower() == 'gzip'):
                    continue

                send_header(header, value)

            self.end_headers()

            self.wfile.write(what_to_send)
        except Exception, e:
            om.out.debug(
                '**Failed to send the data to the browser: %s**' % (e,))
        finally:
            self.wfile.close()

    def _verify_cb(self, conn, cert, errnum, depth, ok):
        """
        Used by set_verify to check that the SSL certificate if valid.
        In our case, we always return True.
        """
        om.out.debug(
            'Got this certificate from remote site: %s' % cert.get_subject())
        # I don't check for certificates, for me, they are always ok.
        return True

    def do_CONNECT(self):
        """
        Handle the CONNECT method.
        This method is not expected to be overwritten.
        To understand what happens here, please read comments for HTTPServerWrapper class
        """
        # Log what we are doing.
        self.log_request(200)
        soc = None

        try:
            try:
                self.wfile.write(self.protocol_version +
                                 " 200 Connection established\r\n\r\n")

                # Now, transform the socket that connects the browser and the
                # proxy to a SSL socket!
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_timeout(5)

                try:
                    ctx.use_privatekey_file(self._uri_opener._proxy_cert)
                except SSL.Error:
                    error = "[proxy error] Couldn't find certificate file %s"
                    error = error % self._uri_opener._proxy_cert
                    om.out.error(error)

                ctx.use_certificate_file(self._uri_opener._proxy_cert)
                ctx.load_verify_locations(self._uri_opener._proxy_cert)

                # Save for later
                browSoc = self.connection

                # Don't demand a certificate
                #
                #   IMPORTANT: This line HAS to be just before the SSL.Connection, it seems that
                #                         any other ctx method modifies the SSL.VERIFY_NONE setting!
                #
                ctx.set_verify(SSL.VERIFY_NONE, self._verify_cb)

                browCon = SSL.Connection(ctx, self.connection)
                browCon.set_accept_state()

                # see HTTPServerWrapper class below
                httpsServer = HTTPServerWrapper(self.__class__, self)
                httpsServer.w3afLayer = self.server.w3afLayer

                om.out.debug("SSL 'self.connection' connection state=" +
                             browCon.state_string())

                conWrap = SSLConnectionWrapper(browCon, browSoc)
                try:
                    httpsServer.process_request(conWrap, self.client_address)
                except SSL.ZeroReturnError, ssl_error:
                    msg = 'Catched SSL.ZeroReturn in do_CONNECT(): %s'
                    om.out.debug(msg % ssl_error)
                except SSL.Error, ssl_error:
                    msg = 'Catched SSL.Error in do_CONNECT(): %s'
                    om.out.debug(msg % ssl_error)
                except TypeError, type_error:
                    # TypeError: shutdown() takes exactly 0 arguments (1 given)
                    # https://bugs.launchpad.net/pyopenssl/+bug/900792
                    msg = 'Socket shutdown is incompatible with pyOpenSSL: %s'
                    om.out.debug(msg % type_error)
                    

            except Exception, e:
                om.out.error('Traceback for this error: ' +
                             str(traceback.format_exc()))

        finally:
            om.out.debug('Closing browser-proxy and proxy-site connections.')

            # Sometimes soc is just None
            if soc:
                soc.close()
            self.connection.close()

    def log_message(self, format, *args):
        """
        I dont want messages written to stderr, please write them to the om.
        """
        message = "Local proxy daemon handling request: %s - %s" % (
            self.address_string(), format % args)
        om.out.debug(message)


class Proxy(Process):
    """
    This class defines a simple HTTP proxy, it is mainly used for "complex"
    plugins.

    You should create a proxy instance like this:
        ws = Proxy( '127.0.0.1', 8080, urlOpener )

    Or like this, if you want to override the proxyHandler (most times you
    want to do it...):
        ws = Proxy( '127.0.0.1', 8080, urlOpener, proxyHandler=pH )

    If the IP:Port is already in use, an exception will be raised while
    creating the ws instance.

    To start the proxy, and given that this is a Process class, you can do this:
        ws.start()

    Or if you don't want a different thread, you can simply call the run method:
        ws.run()

    The proxy handler class is the place where you'll perform all the magic stuff,
    like intercepting requests, modifying them, etc. A good idea if you want to
    code your own proxy handler is to inherit from the proxy handler that is
    already defined in this file (see: w3afProxyHandler).

    What you basically have to do is to inherit from it:
        class myProxyHandler(w3afProxyHandler):

    And redefine the following methods:
        def do_ALL( self )
            Which originally receives a request from the browser, sends it to
            the remote site, receives the response and returns the response to
            the browser. This method is called every time the browser sends a
            new request.

    Things that work:
        - http requests like GET, HEAD, POST, CONNECT
        - https CONNECT ( thanks Sasha! )

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    SSL_CERT = os.path.join(ROOT_PATH, 'core/controllers/daemons/mitm.crt')

    def __init__(self, ip, port, uri_opener, proxy_handler=w3afProxyHandler,
                 proxy_cert=SSL_CERT):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param uri_opener: The uri_opener that will be used to open
            the requests that arrive from the browser
        :param proxy_handler: A class that will know how to handle
            requests from the browser
        :param proxy_cert: Proxy certificate to use, this is needed
            for proxying SSL connections.
        """
        Process.__init__(self)
        self.daemon = True
        self.name = 'ProxyThread'
        
        # Internal vars
        self._server = None
        self._proxy_handler = proxy_handler
        self._running = False
        self._uri_opener = uri_opener

        # User configured parameters
        self._ip = ip
        self._port = port
        self._proxy_cert = proxy_cert

        # Start the proxy server
        try:
            self._server = ProxyServer((self._ip, self._port),
                                       self._proxy_handler)
        except socket.error, se:
            raise ProxyException('Socket error while starting proxy: "%s"'
                                     % se.strerror)
        else:
            # This is here to support port == 0, which will bind to the first
            # available/free port, which we don't know until the server really
            # starts
            self._port = self._server.server_port

    def get_bind_ip(self):
        """
        :return: The IP address where the proxy will listen.
        """
        return self._ip

    def get_bind_port(self):
        """
        :return: The TCP port where the proxy will listen.
        """
        return self._port

    def stop(self):
        """
        Stop the proxy by setting _go to False and creating a new request.
        """
        om.out.debug('Calling stop of proxy daemon.')
        if self._running:
            try:
                # Tell the handler that he must quit
                self._server.stop = True
                conn = httplib.HTTPConnection(self._ip + ':' + str(self._port))
                conn.request("QUIT", "/")
                conn.getresponse()
                om.out.debug('Sent QUIT request.')
            except Exception:
                om.out.debug('Sent QUIT request and got timeout. Proxy server'
                             'marked as closed.')
                self._running = False
            else:
                self._running = False

    def is_running(self):
        """
        :return: True if the proxy daemon is running
        """
        return self._running

    def run(self):
        """
        Starts the proxy daemon; usually this method isn't called directly. In
        most cases you'll call start()
        """
        om.out.debug('Using proxy handler: %s.' % self._proxy_handler)
        self._proxy_handler._uri_opener = self._uri_opener
        self._proxy_handler._uri_opener._proxy_cert = self._proxy_cert

        # Starting to handle requests
        message = 'Proxy server listening on %s:%s.' % (self._ip, self._port)
        om.out.debug(message)
        self._server.w3afLayer = self

        self._running = True
        self._server.serve_forever()
        self._running = False

        # I have to do this to actually KILL the HTTPServer, and free the
        # TCP port
        del self._server

    def get_port(self):
        if self._server is not None:
            return self._server.server_address[1]
    
    def wait_for_start(self):
        while self._server is None or self.get_port() is None:
            time.sleep(0.5)

# I want to use threads to handle all requests.


class ProxyServer(HTTPServer, SocketServer.ThreadingMixIn):
    def serve_forever(self):
        """Handle one request at a time until stopped."""
        self.stop = False
        while not self.stop:
            try:
                self.handle_request()
            except KeyboardInterrupt:
                self.stop = True
                break
        
        msg = 'Exiting proxy server serve_forever(); stop() was successful.'
        om.out.debug(msg)

    def server_bind(self):
        msg = 'Changing socket options of ProxyServer to (socket.SOL_SOCKET,'\
              ' socket.SO_REUSEADDR, 1)'
        om.out.debug(msg)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        HTTPServer.server_bind(self)

# We make SSL Connection look almost exactly as a socket connection.
# Thus, we're able to use the SocketServer framework transparently.


class HTTPServerWrapper(HTTPServer, SocketServer.ThreadingMixIn):
    """
    This is a dummy wrapper around HTTPServer.
    It is intended to be used only through process_request() method
    It also has chainedHandler attribute, which refers to a handler instance
    that was created to handle CONNECT method.

    Client                              Proxy                               Server
       |                                  |                                   |
       | -- CONNECT http://host:port ---> |                                   |
       | <---------- 200 OK ------------  |                                   |
       | -------- Handshake ------------- |                                   |
       |                                  | -- create --> Wrapped Proxy       |
       |                                  |                     |             |
       | --------- (Over SSL) GET /path?params ---------------> |             |
       |                                  | <--- Get info ----  |             |
       |                                  |                     | --- GET --> |

    Due to the wrapper object, the second (wrapped) proxy know almost nothing about
    SSL and works just as with plain sockets.
    Examples of what a second proxy handler would want to know from the original
    one is the CONNECT method path or urlOpener (see spider_man).
    """
    def __init__(self, handler, chainedHandler):
        self.RequestHandlerClass = handler
        self.chainedHandler = chainedHandler


#### And now some helper functions ####
def wrap(socket_obj, ssl_connection, fun, *params):
    """
    A utility function that calls SSL read/write operation and handles errors.
    """
    while True:
        try:
            result = fun(*params)
            break
        except SSL.WantReadError:
            select.select([socket_obj], [], [], 3)
        except SSL.WantWriteError:
            select.select([], [socket_obj], [], 3)
        except SSL.ZeroReturnError:
            # The remote end closed the connection
            ssl_connection.shutdown()
            raise SSL.ZeroReturnError
        except SSL.Error, ssl_error:
            # This is raised when the browser abruptly closes the
            # connection, in order to show the user the "false" w3af MITM certificate
            # and ask if he/she trusts it.
            # Error: [('SSL routines', 'SSL3_READ_BYTES', 'ssl handshake failure')]
            try:
                msg = ssl_error[0][0][2]
            except Exception:
                # Not an error of the type that I was expecting!
                raise ssl_error
            else:
                if msg == 'ssl handshake failure':
                    msg = 'Asking the user about the invalid w3af MITM certificate.' \
                          ' He must accept it.'
                    om.out.debug(msg)
                    ssl_connection.shutdown()
                    raise ssl_error
                else:
                    raise ssl_error

    return result


class SSLConnectionWrapper(object):
    """
    This is a wrapper around an SSL connection which also implements a makefile
    method. Thus, it imitates a socket by an SSL connection.
    """

    def __init__(self, conn, socket):
        self._connection = conn
        self._socket = socket

    def __getattr__(self, name):
#        traceback.print_stack()
        return self._connection.__getattribute__(name)

    def __str__(self):
        return object.__str__(self)

    def __repr__(self):
        return object.__repr__(self)

    def recv(self, amount):
        return wrap(self._socket, self._connection, self._connection.recv, amount)

    def send(self, data):
        # Remember that SSL can only send a string of at most 16384 bytes
        # in one call to "send", so I have to perform this ugly hack:
        amount_sent = 0
        start = 0
        while start < len(data):
            to_send = data[start: start + 16384]
            start += 16384
            amount_sent += wrap(self._socket, self._connection,
                                self._connection.send, to_send)
        return amount_sent

    def makefile(self, perm, buf):
        return SSLConnectionFile(self, socket)


class SSLConnectionFile(object):
    """
    This class pretends to be a file to be used as rfile or wfile in request
    handlers. Actually, it reads and writes data from and to SSL connection
    """

    def __init__(self, sslCon, socket):
        self.closed = False
        self._read_buffer = ''
        self._sslCon = sslCon
        self._socket = socket

    def read(self, amount):
        if len(self._read_buffer) < amount:
            #   We actually want to read ahead in order to have more data in the buffer.
            if amount <= 4096:
                to_read = 4096
            else:
                to_read = amount
            self._read_buffer = self._sslCon.recv(to_read)

        result, self._read_buffer = self._read_buffer[0:
                                                      amount], self._read_buffer[amount:]
        return result

    def write(self, data):
        result = self._sslCon.send(data)
        return result

    def readline(self):
        result = ''
        while True:
            ch = self.read(1)
            result += ch
            if ch == '\n':
                break
        return result

    def flush(self):
        pass

    def close(self):
        pass
