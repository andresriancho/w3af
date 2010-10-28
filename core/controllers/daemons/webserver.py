'''
webserver.py

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
import socket
from core.controllers.threads.w3afThread import w3afThread
import core.controllers.outputManager as om

WEBROOT = 'webroot' + os.path.sep

class webserver(w3afThread):
    '''
    This class defines a simple web server, it is mainly used for "complex"
    attacks like remote file inclusion.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self, ip, port, wr ):
        w3afThread.__init__(self)
        global WEBROOT
        self._ip = ip
        self._port = port
        WEBROOT = wr
        self._server = None
        self._go = True
        self._running = False
    
    def isRunning( self ):
        return self._running
        
    def stop(self):
        om.out.debug('Calling stop of webserver daemon.')
        if self._running:
            self._server.server_close()
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self._ip, self._port))
                s.send('GET / HTTP/1.0\n\n')
                s.close()
            except Exception, e:
                om.out.debug('The webserver ain\'t running and I tried to close it anyway')
            self._running = False
        
    def run(self):
        '''
        Starts the http server.
        '''
        try:
            self._server = w3afHTTPServer((self._ip, self._port), w3afWebHandler )
        except Exception, e:
            om.out.error('Failed to start webserver, error: ' + str(e) )
        else:
            message = 'Web server listening on '+ self._ip + ':'+ str(self._port)
            om.out.debug( message )
            self._running = True
            
            while self._go:
                try:
                    self._server.handle_request()
                except KeyboardInterrupt, k:
                    raise k
                except:
                    self._server.server_close()
                
class w3afWebHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path[1:].count('../'):
            self.send_error(404,'Yeah right...')
        else:
            try:
                f = open( WEBROOT + sep + self.path[1:])
            except IOError:
                try:
                    self.send_error(404,'File Not Found: %s' % self.path)
                except Exception, e:
                    om.out.debug('[webserver] Exception: '+ str(e) )
            else:
                try:
                    self.send_response(200)
                    # This aint nice, but this aint a complete web server implementation
                    # it is only here to serve some files to "victim" web servers
                    type, encoding = mimetypes.guess_type( self.path )
                    if type is not None:
                        self.send_header('Content-type',    type )
                    else:
                        self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
                except Exception, e:
                    om.out.debug('[webserver] Exception: '+ str(e) )
                    
                f.close()

            # Clean up
            self.close_connection = 1
            self.rfile.close()
            self.wfile.close()
        return
    
    def log_message( self, format, *args):
        '''
        I dont want messages written to stderr, please write them to the om.
        '''
        message = "Local httpd - src: %s - %s" %(self.address_string(),format%args) 
        om.out.debug( message )

class w3afHTTPServer( HTTPServer ):
    def server_bind(self):
        om.out.debug('Changing socket options of w3afHTTPServer to (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)')
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        HTTPServer.server_bind( self )
    
if __name__ == "__main__":
    # This doesnt work, I leave it here as a reminder to myself
    ws = webserver( '', 8081 , 'webroot' + os.path.sep )
    ws.start2()
