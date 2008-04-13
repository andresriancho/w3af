"""An asynchronous web server

It doesn't use asyncore / asynchat to make things easier to understand 
(hopefully)

Every time a client connects to the server, the server creates
an object which will manage the dialog with the client :
read what the client has sent, write the response, then close the
connection

An asynchronous server is event-driven : with repeated calls to select()
on the sockets, the server detects which dialog managers have something to 
read and which ones can send something. Since all the sockets are 
non-blocking, the calls to select for reading simply return nothing, without
waiting for something to happen

When a dialog manager has something to read, this means that the client has
sent something. If it's a valid HTTP request, it starts with a request line,
then optional headers, and finally the end-headers sequence (\r\n\r\n)

The dialog manager is not allowed to wait until everything has been received,
it would block all the other connection. So, when it has a block of data to 
read, it buffers it until it finds the end-headers sequence. This may take 
several calls to the read() method of the socket, but as long as the client 
has not sent everything, the server will ask the dialog manager to go on 
reading

When the HTTP request has been received, the dialog manager analyses it : it
parses the first request line to see which HTTP method is used (GET or POST),
what is the URI, translates the URI into a path on the file system. All this
is done in the modules BaseHTTPServer and SimpleHTTPServer in the standard 
library. The request headers are also parsed and stored

Once this is done, the response is ready to be sent to the client. As before,
the dialog manager cannot block the connection to send everything : if the
response is a very big file to download, all the other clients would have to
wait until the file has been sent

So here again the response must be sent piece by piece ; every time the dialog
manager has control, it sends the next piece, and so on until the whole 
response has been sent to the client

To achieve this, the dialog manager holds the response pieces in a list of 
file-like "sources" : StringIO's for the response line and headers, and the 
file object matching the URI if one has been found. When the next source is
None, the dialog manager knows that the whole response has been sent : it
closes the connection and the server removes the dialog manager from its
dictionary

One more thing about POST requests : after the request line and headers have
been received, the dialog manager must go on reading until it has received
a number of bytes specified by the Content-Length header. If the length is too
long to be buffered in memory, a temporary file is created to store the data
before it is parsed by cgi.FieldStorage
"""

import sys
import os
import cStringIO
import socket
import select
import cgi
from CGIHTTPServer import CGIHTTPRequestHandler
import tempfile

class CloseRequest(Exception):
    pass

class EndOfFile(Exception):
    pass

class wfile:
    """A file-like class, with independant reading and writing positions
    (unlike cStringIO)"""

    def __init__(self):
        self.buff = []
        self.pos = 0 # position for reading
    
    def write(self,data):
        # if data comes as unicode string
        # we must not have coersion here 
        # since generally data is already raw 8-bit string
        data = str(data) # if data comes as unicode string
        self.buff.append(data)

    def read(self,nb):
        res = "".join(self.buff)[self.pos:self.pos+nb]
        self.pos += nb
        return res

    def tell(self):
        return self.pos
    
    def seek(self,pos):
        self.pos = pos

    def close(self):
        pass

    def __len__(self):
        return len("".join(self.buff))

class DialogManager(CGIHTTPRequestHandler):

    blocksize = 131072  # size of blocks sent to the socket
    bufsize = 131072    # size of in-memory buffer

    def __init__(self, server, request, client_address):
        self.server = server
        self.request, self.client_address = request, client_address
        self.request.setblocking(0)
        self.incoming = cStringIO.StringIO() # receives the HTTP request
        self.wfile = wfile() # file-like object to write the response
        self.sources = [] # a list of file(-like) objects to pick data from
        self.started = False
        self.request_complete = False
 
    def do_GET(self):
        """Serve a GET request."""
        self.body = {}
        self.pre_handle_data()

    def do_HEAD(self):
        path = self.translate_path(self.path)
        try:
            f = open(path, 'rb')    # always open in binary mode
        except IOError:
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.end_headers()
        self.finish()

    def do_POST(self):
        """Prepare to read the request body"""
        self.cont_length = int(self.headers.getheader('content-length') or 0)
        if self.cont_length > self.bufsize:
            # if the post body is too big, set the buffer to a temporary file
            inc = self.incoming.getvalue()
            self.incoming = tempfile.TemporaryFile()
            self.incoming.write(inc)
        self.finish_POST()

    def finish_POST(self):
        if self.incoming.tell() >= self.cont_length:
            self.incoming.seek(0)
            self.body = cgi.FieldStorage(fp=self.incoming,
                headers=self.headers, environ = {'REQUEST_METHOD':'POST'},
                keep_blank_values = 1)
            self.pre_handle_data()

    def pre_handle_data(self):
        self.incoming.seek(0)
        sys.stdin = self.incoming # compatibility with cgi
        if len(self.wfile):
            self.sources.append(wfile())
            self.wfile = self.sources[-1]
        self.handle_data()
        # after processing, append None to sources, to signal end of request
        self.finish()

    def handle_data(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                self.sources.append(self.list_directory(path))
                return
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')    # always open in binary mode
        except IOError:
            self.send_error(404, "File not found")
            return
        length = os.fstat(f.fileno())[6]
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if self.wfile.tell() + length < self.blocksize:
            self.wfile.write(f.read())
        else:
            self.sources.append(f)

    def copyfile(self,in_file,out_file=None):
        self.sources.append(in_file)

    def handle_read(self):
        # there should be something to read
        try:
            buff = self.request.recv(1024)
        except socket.error:
            raise CloseRequest
        if not buff:
            # the connection is closed
            raise CloseRequest
        self.incoming.write(buff)
        if not self.started:
            # search if the end headers sequence \r\n\r\n has been received
            inc = self.incoming.getvalue()
            pos = inc.find('\r\n\r\n')
            if pos > -1:
                msg = inc[:pos]
                # reset self.incoming to the data received after CRLF
                self.incoming = cStringIO.StringIO()
                self.incoming.write(inc[pos+4:])
                # rfile is used to parse request in BaseHTTPRequestHandler
                self.rfile = cStringIO.StringIO(msg)
                self.started = True
                self.sources = [self.wfile]
                self.raw_requestline = self.rfile.readline()
                if not self.raw_requestline:
                    self.finish()
                elif not self.parse_request(): # An error code has been sent
                    self.finish()
                else:
                    mname = 'do_' + self.command
                    if not hasattr(self, mname):
                        self.send_error(501, "Unsupported method (%r)" 
                            % self.command)
                        self.finish()
                    else:
                        method = getattr(self, mname)
                        method()
        elif hasattr(self,"cont_length"):   # reading POST data
            self.finish_POST()

    def finish(self):
        self.sources.append(None)
        self.request_complete = True
        
    def writable(self):
        """Return True if there is something to write"""
        return self.request_complete

    def handle_write(self):
        """Seek if there is something to write to the client
        The sources are file(-like) objects ; the last one is None,
        signaling the end of the request
        """
        while self.sources:
            if self.sources[0] is None:
                raise CloseRequest
            fobj = self.sources[0]
            pos = fobj.tell()
            buff = fobj.read(self.blocksize)
            if buff:
                break
            fobj.close()
            self.sources[0].close()
            del self.sources[0]
        if buff:
            try:
                sent = self.request.send(buff)
                # set the position in the file to the first byte not sent
                fobj.seek(pos+sent)
            except socket.error:
                raise CloseRequest

class Server:

    def __init__(self, server_address, RequestHandlerClass):
        self.server_name = "SimpleAsyncHTTP/1.0"
        self.server_port = server_address[1]
        self.RequestHandlerClass = RequestHandlerClass
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # exception treatment to avoid some runtime errors if apache
        # or another http server is running. Author: Marcelo Santos Araujo
        try:
            self.socket.bind(server_address)
        except socket.error:
            sys.stderr.write("Address already in use\nAnother server is ")
            sys.stderr.write("running at address %s,%s...\n" %server_address)
            sys.exit()
        self.socket.listen(5)
        self.client_handlers = {}

    def accept_new_client(self):
        try:
            request, client_address = self.socket.accept()
        except socket.error:
            return
        self.client_handlers[request] = self.RequestHandlerClass(self,
            request, client_address)

    def loop(self):
        while True:
            k = self.client_handlers.keys()
            w = [ cl for cl in k if self.client_handlers[cl].writable() ]
            r,w,e = select.select(k+[self.socket],w,k,2)
            for e_socket in e:
                self.close_client(e_socket)
            for r_socket in r:
                if r_socket is self.socket:
                    self.accept_new_client()
                elif r_socket in self.client_handlers.keys():
                    try:
                        self.client_handlers[r_socket].handle_read()
                    except CloseRequest:
                        self.close_client(r_socket)
            for w_socket in w:
                if w_socket in self.client_handlers.keys():
                    try:
                        self.client_handlers[w_socket].handle_write()
                    except CloseRequest:
                        self.close_client(w_socket)

    def close_client(self, client):
        del self.client_handlers[client]
        client.close()

    def close_all(self):
        for s in self.client_handlers:
            s.close()

if __name__=="__main__":
    # launch the server on the specified port
    port = 8081
    print "Asynchronous server running on port %s" %port
    print "Press Ctrl+C to stop"
    server = Server(('', port), DialogManager)
    try:
        server.loop()
    except KeyboardInterrupt:
        server.close_all()
        print 'Ctrl+C pressed. Closing'
