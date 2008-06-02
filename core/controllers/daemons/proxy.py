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

import os
from os import sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import mimetypes
import time
import socket, signal, select
from core.controllers.threads.w3afThread import w3afThread
import core.controllers.outputManager as om
from core.data.parsers.urlParser import *
from core.controllers.threads.threadManager import threadManagerObj as tm
from core.controllers.w3afException import w3afException
from OpenSSL import SSL
import traceback

class proxy(w3afThread):
    '''
    This class defines a simple HTTP proxy, it is mainly used for "complex" plugins.
    
    You should create a proxy instance like this:
        ws = proxy( '127.0.0.1', 8080, urlOpener )
    
    Or like this, if you want to override the proxyHandler (most times you want to do it...):
        ws = proxy( '127.0.0.1', 8080, urlOpener, proxyHandler=pH )
    
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
        self._go = True
        self._running = False
        self._urlOpener = urlOpener
        self._tm = tm
        
        # User configured parameters
        self._ip = ip
        self._port = port
        self._proxyCert = proxyCert
    
    def getBindIP( self ):
        return self._ip
    
    def getBindPort( self ):
        return self._port
        
    def stop(self):
        '''
        Stop the proxy by setting _go to False and creating a new request.
        '''
        om.out.debug('Calling stop of proxy daemon.')
        if self._running:
            self._server.server_close()
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self._ip, self._port))
                s.close()
            except:
                pass
            self._running = False
    
    def isRunning( self ):
        '''
        @return: True if the proxy daemon is running
        '''
        return self._running
    
    def run(self):
        '''
        Starts the proxy daemon; usually this method isn't called directly. In most cases you'll call start2()
        '''
        if self._proxyHandler == None:
            self._proxyHandler = w3afProxyHandler
        
        # Timeout to wait for thread starting
        time.sleep(0.1)
        
        om.out.debug( 'Using proxy handler: ' + str(self._proxyHandler) )
        self._proxyHandler._urlOpener = self._urlOpener
        self._proxyHandler._urlOpener._proxyCert = self._proxyCert
        
        try:
            self._server = HTTPServer( (self._ip, self._port), self._proxyHandler )
        except Exception, e:
            om.out.error('Failed to start proxy server, error: ' + str(e) )
        else:
            message = 'Proxy server listening on '+ self._ip + ':'+ str(self._port)
            om.out.debug( message )
            self._running = True
            
            while self._go:
                try:
                    self._server.handle_request()
                except:
                    self._server.server_close()

class w3afProxyHandler(BaseHTTPRequestHandler):
        
    def _sendToServer( self ):
        '''
        Send a request that arrived from the browser to the remote web server.
        
        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the postdata
            - self.path : Stores the URL that was requested by the browser
        '''
        self.headers['Connection'] = 'close'
        
        # Do the request to the remote server
        if self.headers.dict.has_key('content-length'):
            # POST
            cl = int( self.headers['content-length'] )
            postData = self.rfile.read( cl )
            try:
                res = self._urlOpener.POST( self.path, data=postData, headers=self.headers )
            except w3afException, w:
                om.out.error('The proxy request failed, error: ' + str(w) )
                raise w
            except Exception, e:
                raise e
            return res
            
        else:
            # GET
            url = uri2url( self.path )
            qs = getQueryString( self.path )
            try:
                res = self._urlOpener.GET( url, data=str(qs), headers=self.headers )
            except w3afException, w:
                om.out.error('The proxy request failed, error: ' + str(w) )
                raise w
            except:
                raise
            return res
    
    def _sendError( self, exceptionObj ):
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
            self.wfile.write( 'Proxy error: ' + str(exceptionObj) )
        except Exception, e:
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
            
            for header in res.getHeaders():
                self.send_header( header, res.getHeaders()[header] )
            self.send_header( 'Connection', 'close')
            self.end_headers()
            
            self.wfile.write( res.getBody() )
            self.wfile.close()
        except Exception, e:
            om.out.debug('Failed to send the data to the browser: ' + str(e) )      
    
    def doAll( self ):
        '''
        This method handles GET, POST and HEAD request that were send by the browser.
        '''
        try:
            # Send the request to the remote webserver
            # The request parameters such as the URL, the headers, etc. are stored in "self".
            # Note: This is the way that the HTTPServer and the Handler work in python; this wasn't my choice.
            res = self._sendToServer()
        except Exception, e:
            self._sendError( e )
        else:
            try:
                self._sendToBrowser( res )
            except Exception, e:
                om.out.debug('Exception found while sending response to the browser. Exception description: ' + str(e) )
    
    do_GET = do_POST = do_HEAD = doAll
    
    class TimeoutError (Exception): pass
    def SIGALRM_handler(sig, stack): raise Error("Timeout")
    # Windows signal.SIGALRM doesn't exist
    try:
        signal.signal(signal.SIGALRM, SIGALRM_handler)
    except:
        pass
    
    def _connect_to( self, netloc ):
        '''
        This method is used to handle the CONNECT method. In most cases you shouldnt modify/override it.
        '''
        #print "CONNECT: " + str(netloc)
        i = netloc.find(':')
        if i >= 0:
            host, port = netloc[:i], int(netloc[i+1:])
        else:
            host, port = netloc, 80
        signal.alarm(10)
        try:
            # Connect to the remote site
            try:
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_timeout(5)
                ctx.set_verify(SSL.VERIFY_NONE, self._verify_cb) # Don't demand a certificate
                
                try:
                    ctx.use_privatekey_file ( self._urlOpener._proxyCert )
                except:
                    om.out.error( "[proxy error] Couldn't find certificate file %s"% self._urlOpener._proxyCert )
                    raise

                ctx.use_certificate_file( self._urlOpener._proxyCert )
                ctx.load_verify_locations( self._urlOpener._proxyCert )
                
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                soc.connect((host, port))
                con = SSL.Connection(ctx, soc )
                con.set_connect_state()

                attemp = 0
                while True:
                    try:
                        con.do_handshake()
                        break
                    except SSL.WantReadError:
                        select.select([soc], [], [], 10.0)
                        if attemp == 1:
                            break
                        attemp+=1
                    except SSL.WantWriteError:
                        select.select([], [soc], [], 10.0)
                        if attemp == 1:
                            break
                        attemp+=1
               
            except Exception, e:
                traceback.print_exc()
                print e.message
                om.out.debug( "Remote site ain't using SSL ? Exception: " + str(e) )
                return None
            else:
                om.out.debug( "Remote site IS using SSL, succesfully connected to remote site." )

        finally:
            signal.alarm(0)
        return con
    
    def _verify_cb(self, conn, cert, errnum, depth, ok):
        '''
        Used by set_verify to check that the SSL certificate if valid.
        In our case, we always return True.
        '''
        # This obviously has to be updated
        om.out.debug('Got this certificate from remote site: %s' % cert.get_subject() )
        return ok
        
    def do_CONNECT(self):
        '''
        Handle the CONNECT method.
        '''
        # Log what we are doing.
        self.log_request(200)
        soc = None
        
        try:
            try:
                soc = self._connect_to(self.path)
                if soc:
                    # Send the browser some messages that indicate that the connection to the remote end succeded
                    self.wfile.write(self.protocol_version + " 200 Connection established\r\n\r\n")
                    
#                    self.wfile.write("\r\n")
                    
                    # Now, transform the socket that connects the browser and the proxy to a SSL socket!
                    ctx = SSL.Context(SSL.SSLv23_METHOD)
                    ctx.set_timeout(5)
                    ctx.set_verify(SSL.VERIFY_NONE, self._verify_cb) # Don't demand a certificate
                    
                    try:
                        ctx.use_privatekey_file ( self._urlOpener._proxyCert )
                    except:
                        om.out.error( "[proxy error] Couldn't find certificate file %s"% self._urlOpener._proxyCert )

                    ctx.use_certificate_file( self._urlOpener._proxyCert )
                    ctx.load_verify_locations( self._urlOpener._proxyCert )
                    
                    #normally would be SSL.connection, but we want to be threadsafe
                    self.connection = SSL.Connection(ctx, self.connection )

                    #only works with pyOpenSSL 5.0pre or >
                    self.connection.set_accept_state()
                    om.out.debug("SSL 'self.connection' connection state="+ self.connection.state_string() )
                    
                    # forward data between sockets!
                    self._read_write( self.connection, soc , 300)
            
            except Exception, e:
                om.out.error( 'Traceback for this error: ' + str( traceback.format_exc() ) )
        
        finally:
            om.out.debug('Closing browser-proxy and proxy-site connections.')
            
            # Sometimes soc is just None
            if soc:
                soc.close()
            self.connection.close()
    
    def _analyzeRequestResponse( self, request, response ):
        '''
        This method is called by _read_write and should be implemented by plugins that would like to
        analyze what happends on the proxy ( like spiderMan ).
        '''
        print request
#        print response
        

    def _resend(self, socFrom, socTo, maxIdling=20):
        result = ''
        count = 0
        curSoc = socFrom
        while True:
            try:
                buf = socFrom.recv(4096)
                if not buf: break
                curSoc = socTo
                count=0
                socTo.send(buf)
                
            except SSL.WantReadError, wre:
                count+=1
                select.select([curSoc], [], [], 3)
                if count == maxIdling:
                    break
            except SSL.WantWriteError, wwe:
                count+=1
                select.select([], [curSoc], [], 3)
                if count == maxIdling:
                    break
            
    def _read_write(self, browserConnection, siteConnection, max_idling=20, sslSocket=None):
        '''
        - Read from the socket that is connected to the browser
        - Write the received data to the socket that is connected to the remote site
        - Read from the socket that is connected to the remote site
        - Write the received data back to the browser
        
        All this using select in a loop.
        '''
        self._resend(browserConnection, siteConnection)
        self._resend(siteConnection, browserConnection)

    def log_message( self, format, *args):
        '''
        I dont want messages written to stderr, please write them to the om.
        '''
        message = "Local proxy daemon handling request: %s - %s" % (self.address_string(),format%args) 
        om.out.debug( message )

