"""
Simple socket server that will return the first 1024 bytes you send to it 
in upper case.

http://docs.python.org/2/library/socketserver.html
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
    def __init__(self, handler=UpperTCPHandler):
        super(UpperDaemon, self).__init__()
        self.daemon = True
        self.server = None
        self.handler = handler
        
    def run(self):
        # Zero in the port means: bind to any free port
        self.server = SocketServer.TCPServer(('127.0.0.1', 0),
                                             self.handler)
    
        self.server.serve_forever()
    
    def get_port(self):
        if self.server is not None:
            return self.server.server_address[1]
    
    def wait_for_start(self):
        while self.server is None or self.get_port() is None:
            time.sleep(0.5)
    
    @property
    def requests(self):
        return self.server.RequestHandlerClass.requests
    
    def shutdown(self):
        self.server.RequestHandlerClass.requests = []
        self.server.shutdown()
        
