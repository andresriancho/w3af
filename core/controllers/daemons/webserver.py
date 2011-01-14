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

import BaseHTTPServer
import mimetypes
import os
import socket, threading, select

import core.controllers.outputManager as om

# Created servers
_servers = {}
# Used by w3afWebHandler to serve data
WEBROOT = 'webroot' + os.path.sep
# Server timeout
SERVER_TIMEOUT = 3 * 60 # seconds

def start_webserver(ip, port, webroot=None):
    '''Create a http server deamon. The returned instance is unique for <ip>
    and <port>.
    
    @param ip: IP number
    @param port: Port number
    @param webroot: webserver's root directory
    @return: A local webserver instance bound to the
        requested address (<ip>, <port>)
    '''
    global WEBROOT
    if webroot is None:
        webroot = WEBROOT # Use default
    else:
        WEBROOT = webroot # Override default

    web_server = _get_inst(ip, port)

    if web_server is None or web_server.is_down():
        web_server = w3afHTTPServer((ip, port), w3afWebHandler)
        global _servers
        _servers[(ip, port)] = web_server
        # Start server!
        server_thread = threading.Thread(target=web_server.serve_forever)
        server_thread.setDaemon(True)
        server_thread.start()

def is_running(ip, port):
    '''
    Given `ip` and `port` determine if a there's a bound webserver instance
    '''
    web_server = _get_inst(ip, port)
    if web_server is None:
        return False
    return not web_server.is_down()

def _get_inst(ip, port):
    '''
    Return a previously created instance bound to `ip` and `port`. Otherwise
    return None.
    '''
    return _servers.get((ip, port), None)


class w3afHTTPServer(BaseHTTPServer.HTTPServer):
    '''Must of the behavior added here is included in 
    '''

    def __init__(self, server_address, RequestHandlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.__is_shut_down = threading.Event()
        self.__shutdown_request = False

    def is_down(self):
        return self.__shutdown_request

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__is_shut_down.clear()
        try:
            while not self.__shutdown_request:
                self.handle_request()
        finally:
            ##self.__shutdown_request = False
            self.__is_shut_down.set()

    def handle_request(self):
        """Handle one request, possibly blocking."""

        fd_sets = select.select([self], [], [], SERVER_TIMEOUT)
        if not fd_sets[0]:
            self.server_close()
            self.__shutdown_request = True
            return
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.close_request(request)

    def server_bind(self):
        om.out.debug('Changing socket options of w3afHTTPServer to (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)')
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        BaseHTTPServer.HTTPServer.server_bind(self)


class w3afWebHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path[1:].count('../') or self.path[1:].count('..\\'):
            self.send_error(404, 'Yeah right...')
        else:
            try:
                f = open(WEBROOT + os.path.sep + self.path[1:])
            except IOError:
                try:
                    self.send_error(404, 'File Not Found: %s' % self.path)
                except Exception, e:
                    om.out.debug('[webserver] Exception: ' + str(e))
            else:
                try:
                    self.send_response(200)
                    # This aint nice, but this aint a complete web server implementation
                    # it is only here to serve some files to "victim" web servers
                    type, encoding = mimetypes.guess_type(self.path)
                    if type is not None:
                        self.send_header('Content-type', type)
                    else:
                        self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
                except Exception, e:
                    om.out.debug('[webserver] Exception: ' + str(e))

                f.close()

            # Clean up
            self.close_connection = 1
            self.rfile.close()
            self.wfile.close()
        return

    def log_message(self, format, *args):
        '''
        I dont want messages to be written to stderr, please write them
        to the om.
        '''
        message = "Local httpd - src: %s - %s" % \
            (self.address_string(), format % args)
        om.out.debug(message)


if __name__ == "__main__":
    # This doesnt work, I leave it here as a reminder to myself
    ws = start_webserver('', 8081 , 'webroot' + os.path.sep)
    ws.start2()
