"""
webserver.py

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
import BaseHTTPServer
import mimetypes
import os
import socket
import threading
import select
import time

import w3af.core.controllers.output_manager as om

# Created servers
_servers = {}

# Server timeout in seconds
SERVER_TIMEOUT = 3 * 60


def is_running(ip, port):
    """
    Given `ip` and `port` determine if a there's a bound webserver instance
    """
    web_server = _get_inst(ip, port)
    if web_server is None:
        return False
    return not web_server.is_down()


def _get_inst(ip, port):
    """
    Return a previously created instance bound to `ip` and `port`. Otherwise
    return None.
    """
    return _servers.get((ip, port), None)


class w3afHTTPServer(BaseHTTPServer.HTTPServer):
    """
    Most of the behavior added here is included in
    """

    def __init__(self, server_address, webroot, RequestHandlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, server_address,
                                           RequestHandlerClass)
        self.webroot = webroot
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
            except Exception:
                self.handle_error(request, client_address)
                self.close_request(request)

    def server_bind(self):
        msg = 'Changing socket options of w3afHTTPServer to (socket.SOL_SOCKET'\
              ', socket.SO_REUSEADDR, 1)'
        om.out.debug(msg)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        BaseHTTPServer.HTTPServer.server_bind(self)

    def get_port(self):
        try:
            return self.server_address[1]
        except:
            return None
    
    def wait_for_start(self):
        while self.get_port() is None:
            time.sleep(0.5)

class w3afWebHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path[1:].count('../') or self.path[1:].count('..\\'):
            self.send_error(403, 'Yeah right...')
        else:
            try:
                f = open(self.server.webroot + os.path.sep + self.path[1:])
            except IOError:
                try:
                    self.send_error(404, 'File Not Found: %s' % self.path)
                except Exception, e:
                    om.out.debug('[webserver] Exception: ' + str(e))
            else:
                try:
                    self.send_response(200)
                    # This isn't nice, but this is NOT a complete web server implementation
                    # it is only here to serve some files to "victim" web servers
                    content_type, encoding = mimetypes.guess_type(self.path)
                    if content_type is not None:
                        self.send_header('Content-type', content_type)
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

    def log_message(self, fmt, *args):
        """
        I dont want messages to be written to stderr, please write them
        to the om.
        """
        message = "webserver.py: %s - %s" % (self.address_string(), fmt % args)
        om.out.debug(message)


def start_webserver(ip, port, webroot, handler=w3afWebHandler):
    """Create a http server deamon. The returned instance is unique for <ip>
    and <port>.

    :param ip: IP address where to bind
    :param port: Port number
    :param webroot: webserver's root directory
    :return: A local webserver instance bound to the requested address (<ip>, <port>)
    """
    server_thread = _get_inst(ip, port)

    if server_thread is None or server_thread.is_down():
        web_server = w3afHTTPServer((ip, port), webroot, handler)
        _servers[(ip, port)] = web_server
        # Start server!
        server_thread = threading.Thread(target=web_server.serve_forever)
        server_thread.name = 'WebServer'
        server_thread.daemon = True
        server_thread.start()

    return server_thread

def start_webserver_any_free_port(ip, webroot, handler=w3afWebHandler):
    """Create a http server deamon in any free port available.

    :param ip: IP address where to bind
    :param webroot: webserver's root directory
    :return: A local webserver instance and the port where it's listening
    """
    web_server = w3afHTTPServer((ip, 0), webroot, handler)

    # Start server!
    server_thread = threading.Thread(target=web_server.serve_forever)
    server_thread.name = 'WebServer'
    server_thread.daemon = True
    server_thread.start()

    web_server.wait_for_start()

    return server_thread, web_server.get_port()