'''
proxy.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

import cStringIO
import traceback
import time
import socket
import select
import httplib
import SocketServer
from OpenSSL import SSL
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from core.controllers.threads.w3afThread import w3afThread
from core.controllers.threads.threadManager import threadManagerObj as tm
from core.controllers.w3afException import w3afException, w3afProxyException
import core.controllers.outputManager as om
from core.data.parsers.urlParser import url_object
from core.data.request.fuzzableRequest import fuzzableRequest

class proxy(w3afThread):
    '''
    This class defines a simple HTTP proxy, it is mainly used for "complex" plugins.
    
    You should create a proxy instance like this:
        ws = proxy( '127.0.0.1', 8080, urlOpener )
    
    Or like this, if you want to override the proxyHandler (most times you want to do it...):
        ws = proxy( '127.0.0.1', 8080, urlOpener, proxyHandler=pH )
    
    If the IP:Port is already in use, an exception will be raised while creating the ws instance.
    
    To start the proxy, and given that this is a w3afThread class, you can do this:
        ws.start2()
        
    Or if you don't want a different thread, you can simply call the run method:
        ws.run()
    
    The proxy handler class is the place where you'll perform all the magic stuff, like intercepting requests, modifying
    them, etc. A good idea if you want to code your own proxy handler is to inherit from the proxy handler that 
    is already defined in this file (see: w3afProxyHandler).
    
    What you basically have to do is to inherit from it:
        class myProxyHandler(w3afProxyHandler):
        
    And redefine the following methods:
        def doAll( self )
            Which originally receives a request from the browser, sends it to the remote site, receives the response
            and returns the response to the browser. This method is called every time the browser sends a new request.
    
    Things that work:
        - http requests like GET, HEAD, POST, CONNECT
        - https CONNECT ( thanks Sasha! )
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__( self, ip, port, urlOpener, proxyHandler=None, proxyCert = 'core/controllers/daemons/mitm.crt' ):
        '''
        @parameter ip: IP address to bind
        @parameter port: Port to bind
        @parameter urlOpener: The urlOpener that will be used to open the requests that arrive from the browser
        @parameter proxyHandler: A class that will know how to handle requests from the browser
        @parameter proxyCert: Proxy certificate to use, this is needed for proxying SSL connections.
        '''
        w3afThread.__init__(self)

        # Internal vars
        self._server = None
        self._proxyHandler = proxyHandler
        self._running = False
        self._urlOpener = urlOpener
        self._tm = tm
        
        # User configured parameters
        self._ip = ip
        self._port = port
        self._proxyCert = proxyCert
        
        # Start the proxy server
        try:
            self._server = ProxyServer( (self._ip, self._port), self._proxyHandler )
        except socket.error, se:
            if se[0] == 98:
                raise w3afProxyException('Address already in use ' + self._ip + ':' + str(self._port))
            else:
                raise w3afException(str(se))
    
    def getBindIP( self ):
        '''
        @return: The IP address where the proxy will listen.
        '''
        return self._ip
    
    def getBindPort( self ):
        '''
        @return: The TCP port where the proxy will listen.
        '''
        return self._port
        
    def stop(self):
        '''
        Stop the proxy by setting _go to False and creating a new request.
        '''
        om.out.debug('Calling stop of proxy daemon.')
        if self._running:
            try:
                # Tell the proxy that he must quit
                self._server.stop = True
                conn = httplib.HTTPConnection(self._ip+':'+str(self._port))
                conn.request("QUIT", "/")
                conn.getresponse()
                om.out.debug('Sent QUIT request.')
            except Exception:
                om.out.debug('Sent QUIT request and got timeout. Proxy server closed.')
                self._running = False
            else:
                self._running = False
        else:
            om.out.debug('You called stop() on a proxy daemon that isn\'t running.')
    
    def isRunning( self ):
        '''
        @return: True if the proxy daemon is running
        '''
        return self._running
    
    def run(self):
        """
        Starts the proxy daemon; usually this method isn't called directly. In most cases you'll call start2()
        """
        if self._proxyHandler is None:
            self._proxyHandler = w3afProxyHandler
        
        # Timeout to wait for thread starting
        time.sleep(0.1)
        
        om.out.debug( 'Using proxy handler: ' + str(self._proxyHandler) )
        self._proxyHandler._urlOpener = self._urlOpener
        self._proxyHandler._urlOpener._proxyCert = self._proxyCert
        
        # Starting to handle requests
        message = 'Proxy server listening on '+ self._ip + ':'+ str(self._port)
        om.out.debug( message )
        self._server.w3afLayer = self
        self._running = True
        self._server.serve_forever()
        
        # We aren't running anymore
        self._running = False
        # I have to do this to actually KILL the HTTPServer, and free the TCP port
        del self._server


class w3afProxyHandler(BaseHTTPRequestHandler):
    
    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.
        
        I override this because I'm going to use ONE handler for all the methods (except CONNECT).
        """
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        
        try:
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
                self.doAll()
        except Exception,  e:
            ### FIXME: Maybe I should perform some more detailed error handling...
            om.out.debug('An exception ocurred in w3afProxyHandler.handle_one_request() :' + str(e) )

    def _getPostData(self):
        '''
        @return: Post data preserving rfile
        '''
        postData = None
        if self.headers.dict.has_key('content-length'):
            cl = int(self.headers['content-length'])
            postData = self.rfile.read(cl)
            # rfile is not seekable, so a little trick
            if not hasattr(self.rfile, 'reset'):
                rfile = cStringIO.StringIO(postData)
                self.rfile = rfile
            self.rfile.reset()
        return postData

    def _createFuzzableRequest(self):
        '''
        Based on the attributes, return a fuzzable request object.
        
        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the postdata
            - self.path : Stores the URL that was requested by the browser
        '''
        # See HTTPWrapperClass
        if hasattr(self.server, 'chainedHandler'):
            basePath = "https://" + self.server.chainedHandler.path
            path = basePath + self.path
        else:
            path = self.path

        fuzzReq = fuzzableRequest()
        fuzzReq.setURI(url_object(path))
        fuzzReq.setHeaders(self.headers.dict)
        fuzzReq.setMethod(self.command)
        postData = self._getPostData()
        if postData:
            fuzzReq.setData(postData)
        return fuzzReq

    def doAll( self ):
        '''
        This method handles EVERY request that were send by the browser.
        '''
        try:
            # Send the request to the remote webserver
            # The request parameters such as the URL, the headers, etc. are stored in "self".
            # Note: This is the way that the HTTPServer and the Handler work in python; this wasn't my choice.
            res = self._sendToServer()
        except Exception, e:
            self._sendError( e, trace=str(traceback.format_exc()) )
        else:
            try:
                self._sendToBrowser( res )
            except Exception, e:
                om.out.debug('Exception found while sending response to the browser. Exception description: ' + str(e) )


    def _sendToServer( self,  grep=False ):
        '''
        Send a request that arrived from the browser to the remote web server.
        
        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the postdata
            - self.path : Stores the URL that was requested by the browser
        '''
        self.headers['Connection'] = 'close'

        path = self.path

        # See HTTPWrapperClass
        if hasattr(self.server, 'chainedHandler'):
            basePath = "https://" + self.server.chainedHandler.path
            path = basePath + path
        
        # Do the request to the remote server
        if self.headers.dict.has_key('content-length'):
            # most likely a POST request
            postData = self._getPostData()

            try:
                httpCommandMethod = getattr( self._urlOpener, self.command )
                res = httpCommandMethod( path, data=postData, headers=self.headers )
            except w3afException, w:
                om.out.error('The proxy request failed, error: ' + str(w) )
            except Exception, e:
                raise e
            else:
                return res
            
        else:
            # most likely a GET request

            uri_instance = url_object(path) 
            qs = uri_instance.getQueryString()
            try:
                httpCommandMethod = getattr( self._urlOpener, self.command )
                res = httpCommandMethod(uri_instance, data=str(qs), headers=self.headers,  grepResult=grep )
            except w3afException, w:
                traceback.print_exc()
                om.out.error('The proxy request failed, error: ' + str(w) )
                raise w
            except Exception, e:
                traceback.print_exc()
                raise e
            else:
                return res
    
    def _sendError( self, exceptionObj, trace=None ):
        '''
        Send an error to the browser.
        
        Important methods used here:
            - self.send_header : Sends a header to the browser
            - self.end_headers : Ends the headers section
            - self.wfile : A file like object that represents the body of the response
        '''
        try:
            self.send_response( 400 )
            self.send_header( 'Connection', 'close')
            self.send_header( 'Content-type', 'text/html')      
            self.end_headers()
            # FIXME: Make this error look nicer
            self.wfile.write( 'w3af proxy error: ' + str(exceptionObj) + '<br/><br/>')
            if trace:
                self.wfile.write( 'Traceback for this error: <br/><br/>' + trace.replace('\n','<br/>') )

        except Exception, e:
            traceback.print_exc()
            om.out.debug('An error ocurred in proxy._sendError(). Maybe the browser closed the connection?')
            om.out.debug('Exception: ' + str(e) )
        self.wfile.close()
    
    def _sendToBrowser( self, res ):
        '''
        Send a response that was sent by the remote web server to the browser

        Important methods used here:
            - self.send_header : Sends a header to the browser
            - self.end_headers : Ends the headers section
            - self.wfile : A file like object that represents the body of the response
        '''
        try:
            self.send_response( res.getCode() )

            what_to_send = res.getBody()
            
            for header in res.getHeaders():
                if header == 'transfer-encoding' and res.getHeaders()[header] == 'chunked':
                    # don't send this header, and send the content-length instead
                    self.send_header( 'content-length', str(len(what_to_send)) )
                else:    
                    self.send_header( header, res.getHeaders()[header] )
            
            self.send_header( 'Connection', 'close')
            self.end_headers()
            
            self.wfile.write(what_to_send)
            self.wfile.close()
        except Exception, e:
            om.out.debug('Failed to send the data to the browser: ' + str(e) )

    def _verify_cb(self, conn, cert, errnum, depth, ok):
        '''
        Used by set_verify to check that the SSL certificate if valid.
        In our case, we always return True.
        '''
        om.out.debug('Got this certificate from remote site: %s' % cert.get_subject() )
        # I don't check for certificates, for me, they are always ok.
        return True

    def do_CONNECT(self):
        '''
        Handle the CONNECT method.
        This method is not expected to be overwritten.
        To understand what happens here, please read comments for HTTPServerWrapper class
        '''
        # Log what we are doing.
        self.log_request(200)
        soc = None
        
        try:
            try:
                self.wfile.write(self.protocol_version + " 200 Connection established\r\n\r\n")
                
                # Now, transform the socket that connects the browser and the proxy to a SSL socket!
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_timeout(5)
                
                try:
                    ctx.use_privatekey_file ( self._urlOpener._proxyCert )
                except:
                    om.out.error( "[proxy error] Couldn't find certificate file %s"% self._urlOpener._proxyCert )
                
                ctx.use_certificate_file( self._urlOpener._proxyCert )
                ctx.load_verify_locations( self._urlOpener._proxyCert )
                
                # Save for later
                browSoc = self.connection
                
                # Don't demand a certificate
                #
                #   IMPORTANT: This line HAS to be just before the SSL.Connection, it seems that 
                #                         any other ctx method modifies the SSL.VERIFY_NONE setting!
                #
                ctx.set_verify(SSL.VERIFY_NONE, self._verify_cb)
                
                browCon = SSL.Connection(ctx, self.connection )
                browCon.set_accept_state()

                # see HTTPServerWrapper class below
                httpsServer = HTTPServerWrapper(self.__class__, self)
                httpsServer.w3afLayer = self.server.w3afLayer
            
                om.out.debug("SSL 'self.connection' connection state="+ browCon.state_string() )
                
                conWrap = SSLConnectionWrapper(browCon, browSoc)
                try:
                    httpsServer.process_request(conWrap, self.client_address)
                except SSL.ZeroReturnError, ssl_error:
                    om.out.debug('Catched SSL.ZeroReturn in do_CONNECT(): ' + str(ssl_error) )
                except SSL.Error, ssl_error:
                    om.out.debug('Catched SSL.Error in do_CONNECT(): ' + str(ssl_error) )
            
            except Exception, e:
                om.out.error( 'Traceback for this error: ' + str( traceback.format_exc() ) )
        
        finally:
            om.out.debug('Closing browser-proxy and proxy-site connections.')
            
            # Sometimes soc is just None
            if soc:
                soc.close()
            self.connection.close()

    def log_message( self, format, *args):
        '''
        I dont want messages written to stderr, please write them to the om.
        '''
        message = "Local proxy daemon handling request: %s - %s" % (self.address_string(), format%args) 
        om.out.debug( message )

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
        om.out.debug('Exiting proxy server serve_forever(); stop() was successful.')
                
    def server_bind(self):
        om.out.debug('Changing socket options of ProxyServer to (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)')
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        HTTPServer.server_bind( self )                

# We make SSL Connection look almost exactly as a socket connection. 
# Thus, we're able to use the SocketServer framework transparently.
class HTTPServerWrapper(HTTPServer, SocketServer.ThreadingMixIn):
    '''
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
    one is the CONNECT method path or urlOpener (see spiderMan).
    '''
    def __init__(self, handler, chainedHandler):
        self.RequestHandlerClass = handler
        self.chainedHandler = chainedHandler

        
#### And now some helper functions ####        
def wrap(socket_obj, ssl_connection, fun, *params):
    '''
    A utility function that calls SSL read/write operation and handles errors.
    '''
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
                    om.out.debug('Asking the user about the invalid w3af MITM certificate. He must accept it.')
                    ssl_connection.shutdown()
                    raise ssl_error
                else:
                    raise ssl_error


    return result
    

class SSLConnectionWrapper(object):
    '''
    This is a wrapper around an SSL connection which also implements a makefile method.
    Thus, it imitates a socket by an SSL connection.
    '''

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
        
    def recv( self, amount):
        return wrap(self._socket, self._connection, self._connection.recv, amount)

    def send( self, data ):
        # Remember that SSL can only send a string of at most 16384 bytes
        # in one call to "send", so I have to perform this ugly hack:
        amount_sent = 0
        start = 0
        while start < len(data):
            to_send = data[start: start + 16384]
            start += 16384
            amount_sent += wrap(self._socket, self._connection, self._connection.send, to_send)
        return amount_sent
           
    def makefile(self, perm, buf):
        return SSLConnectionFile( self, socket )

class SSLConnectionFile:
    '''
    This class pretends to be a file to be used as rfile or wfile in request handlers.
    Actually, it reads and writes data from and to SSL connection
    '''
    
    def __init__(self, sslCon, socket):
        self.closed = False
        self._read_buffer = ''
        self._sslCon = sslCon
        self._socket = socket

    def read( self, amount ):
        if len(self._read_buffer) < amount:
            #   We actually want to read ahead in order to have more data in the buffer.
            if amount <= 4096:
                to_read = 4096
            else:
                to_read = amount
            self._read_buffer = self._sslCon.recv( to_read )

        result, self._read_buffer = self._read_buffer[0:amount], self._read_buffer[amount:]
        return result
    
    def write( self, data ):
        result =  self._sslCon.send(data)
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
