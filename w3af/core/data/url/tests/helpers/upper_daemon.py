"""
upper_daemon.py

Copyright 2015 Andres Riancho

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
import SocketServer
import threading
import time


class UpperTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


class UpperDaemon(threading.Thread):
    """
    Simple socket server that will return the first 1024 bytes you send to it
    in upper case.

    Echo the data sent by the client, but upper case it first.

    http://docs.python.org/2/library/socketserver.html
    """
    def __init__(self, handler=UpperTCPHandler):
        super(UpperDaemon, self).__init__()
        self.daemon = True
        self.server = None
        self.handler = handler
        self.server_address = ('127.0.0.1', 0)

    def run(self):
        # Zero in the port means: bind to any free port
        self.server = SocketServer.TCPServer(self.server_address,
                                             self.handler)
    
        try:
            self.server.serve_forever()
        except AttributeError:
            # Catch some ugly tracebacks on shutdown
            # https://circleci.com/gh/andresriancho/w3af/1568
            pass

    def get_host_port(self):
        return '127.0.0.1:%s' % self.get_port()

    def get_port(self):
        if self.server is not None:
            port = self.server.server_address[1]
            if port != 0:
                return port
    
    def wait_for_start(self):
        while self.server is None or self.get_port() is None:
            time.sleep(0.5)
    
    @property
    def requests(self):
        return self.server.RequestHandlerClass.requests
    
    def shutdown(self):
        self.server.RequestHandlerClass.requests = []
        self.server.shutdown()


class ThreadingUpperDaemon(UpperDaemon):
    def run(self):
        # Zero in the port means: bind to any free port
        self.server = ThreadingServer(self.server_address, self.handler)
        self.server.serve_forever()


class ThreadingServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True

    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, handler_klass):
        SocketServer.TCPServer.__init__(self, server_address, handler_klass)