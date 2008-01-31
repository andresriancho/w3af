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
    
    You should call it like this:
        ws = proxy( '127.0.0.1', 8080, urlOpener )
        ws.start2()
    
    Or like this, if you want to override the proxyHandler (most times you want to do it...):
        ws = proxy( '127.0.0.1', 8080, urlOpener, proxyHandler=pH )
        ws.start2()
    
    Where pH is a class like this:
        class w3afProxyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                ...
                ...
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self, ip, port, urlOpener, proxyHandler=None, proxyCert = 'core/controllers/daemons/mitm.crt' ):
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
        
    def stop(self):
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
        return self._running
    
    def run(self):
        '''
        Starts the proxy daemon.
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
        '''
        try:
            self.send_response( 400 )
            self.send_header( 'Connection', 'close')
            self.send_header( 'Content-type', 'text/html')      
            self.end_headers()
            self.wfile.write( 'Proxy error: ' + str(exceptionObj) )
        except Exception, e:
            om.out.debug('An error ocurred in proxy._sendError(). Maybe the browser closed the connection?')
            om.out.debug('Exception: ' + str(e) )
        self.wfile.close()
    
    def _sendToBrowser( self, res ):
        '''
        Send a response to the browser
        '''
        # return the response to the browser
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
        try:
            # Send the request to the remote webserver
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
    def SIGALRM_handler(sig, stack): raise TimeoutError()
    # Windows signal.SIGALRM doesn't exist
    try:
        signal.signal(signal.SIGALRM, SIGALRM_handler)
    except:
        pass
    
    def _connect_to( self, netloc ):
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
                soc = SSL.Connection(ctx, soc )
                soc.connect( (host, port) )
                
                om.out.debug("SSL 'soc' connection state="+ soc.state_string() )
                
            except Exception, e:
                om.out.debug( "Remote site ain't using SSL ? Exception: " + str(e) )
                return None
            else:
                om.out.debug( "Remote site IS using SSL, succesfully connected to remote site." )

        finally:
            signal.alarm(0)
        return soc
    
    def _verify_cb(self, conn, cert, errnum, depth, ok):
        '''
        Used by set_verify
        '''
        # This obviously has to be updated
        om.out.debug('Got this certificate from remote site: %s' % cert.get_subject() )
        return ok
        
    def do_CONNECT(self):
        # Log what we are doing.
        self.log_request(200)
        soc = None
        
        try:
            try:
                soc = self._connect_to(self.path)
                if soc:
                    # Send the browser some messages that indicate that the connection to the remote end succeded
                    self.wfile.write(self.protocol_version + " 200 Connection established\r\n")
                    self.wfile.write("\r\n")
                    
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
        print 'len req:',len(request)
        print 'len res:', len(response)
        
    def _read_write(self, browserConnection, siteConnection, max_idling=20, sslSocket=None):
        '''
        - Read from the socket that is connected to the browser
        - Write the received data to the socket that is connected to the remote site
        - Read from the socket that is connected to the remote site
        - Write the received data back to the browser
        
        All this using select in a loop.
        '''
        # Do this forever
        while True:
        
            om.out.debug('Read from the browser')
            count = 0
            request = ''
            while count < max_idling:
                try:
                    request += browserConnection.recv(8192)
                    count = 0
                    print 'got request part'
                except SSL.WantReadError:
                    print 'wr'
                    count += 1
                    select.select([browserConnection],[],[],3)
                except SSL.WantWriteError:
                    print 'ww'
                    count += 1
                    select.select([],[browserConnection],[],3)
                except SSL.ZeroReturnError:
                    #nothing else to be read
                    print 'zero'
                    break
                except Exception, e:
                    om.out.debug('Closing browserConnection because of exception:' + str(e) )
                    browserConnection.close()
                    siteConnection.close()
                    return
            
            if count == max_idling:
                om.out.debug('Closing browserConnection because of exception:' + str(e) )
                browserConnection.close()
                siteConnection.close()
                return
                
            om.out.debug('Ok.')
            
            om.out.debug('Write to the siteConnection')
            count = 0
            while count != max_idling:
                try:
                    written = siteConnection.send(request)
                    count = 0
                    break
                except SSL.WantWriteError:
                    count += 1
                    select.select([],[siteConnection],[],3)
                except SSL.WantReadError:
                    count += 1
                    select.select([siteConnection],[],[],3)
                except Exception, e:
                    om.out.debug('Closing siteConnection because of exception:' + str(e) )
                    browserConnection.close()
                    siteConnection.close()
                    return
            
            if count == max_idling:
                om.out.debug('Closing siteConnection because of exception:' + str(e) )
                browserConnection.close()
                siteConnection.close()
                return
            
            om.out.debug('Ok.')
            
            om.out.debug('Read from the remote website')
            count = 0
            response = ''
            while count < max_idling:
                try:
                    response += siteConnection.recv(8192)
                    count = 0
                except SSL.WantReadError:
                    count += 1
                    select.select([siteConnection],[],[],3)
                except SSL.WantWriteError:
                    count += 1
                    select.select([],[siteConnection],[],3)
                except SSL.ZeroReturnError:
                    #nothing else to be read
                    break
                except Exception, e:
                    om.out.debug('Closing siteConnection because of exception:' + str(e) )
                    browserConnection.close()
                    siteConnection.close()
                    return
            
            if count == max_idling:
                om.out.debug('Closing siteConnection because of exception:' + str(e) )
                browserConnection.close()
                siteConnection.close()
                return
            
            self._analyzeRequestResponse( request, response )
            om.out.debug('Ok.')
            
            om.out.debug('Write to the browserConnection (forwarding response from site to the browser)')
            count = 0
            while count != max_idling:
                try:
                    response = browserConnection.write(response)
                    count = 0
                    break
                except SSL.WantWriteError:
                    count += 1
                    select.select([browserConnection,],[],[],3)
                except SSL.WantReadError:
                    count += 1
                    select.select([],[browserConnection],[],3)
                except Exception, e:
                    om.out.debug('Closing browserConnection because of exception:' + str(e) )
                    browserConnection.close()
                    siteConnection.close()
                    return
            
            if count == max_idling:
                om.out.debug('Closing browserConnection because of exception:' + str(e) )
                browserConnection.close()
                siteConnection.close()
                return
        om.out.debug('Ok.')
        
    def log_message( self, format, *args):
        '''
        I dont want messages written to stderr, please write them to the om.
        '''
        message = "Local proxy daemon handling request: %s - %s" % (self.address_string(),format%args) 
        om.out.debug( message )

