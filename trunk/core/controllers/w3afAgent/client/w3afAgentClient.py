#!/usr/bin/env python
import time
import select
import thread
import getopt
import os
import sys
import socket
import struct
import threading

def is_routable(address):
    # Splitting the address in its 4 components.
    first, second, junk1, junk2 = address.split('.')
    # Testing the address against the given intervals.
    if (first in ['10', '127']
        or (first == '172' and second >= '16' and second <= '31')
        or ((first, second) == ('192', '168'))):
        return 0
    return 1

def is_port(port):
    return (port > 0) and (port < 65536)

# SOCKS 4 protocol constant values.
SOCKS_VERSION = 4

COMMAND_CONNECT = 1
COMMAND_BIND = 2
COMMANDS = [
    COMMAND_CONNECT,
    COMMAND_BIND
    ]

REQUEST_GRANTED              = 90
REQUEST_REJECTED_FAILED      = 91
REQUEST_REJECTED_NO_IDENTD    = 92
REQUEST_REJECTED_IDENT_FAILED   = 93

# Sockets protocol constant values.
ERR_CONNECTION_RESET_BY_PEER    = 10054
ERR_CONNECTION_REFUSED        = 10061


# For debugging only.
def now():
    return time.ctime(time.time())

# Exception class for file errors
class FileError(Exception): pass

# Exception classes for the server
class SocksError(Exception): pass
class Connection_Closed(SocksError): pass
class Bind_TimeOut_Expired(SocksError): pass
class Request_Error(SocksError): pass

class Client_Connection_Closed(Connection_Closed): pass
class Remote_Connection_Closed(Connection_Closed): pass
class Remote_Connection_Failed(Connection_Closed): pass
class Remote_Connection_Failed_Invalid_Host(Remote_Connection_Failed): pass

class Request_Failed(Request_Error): pass
class Request_Failed_No_Identd(Request_Failed): pass
class Request_Failed_Ident_failed(Request_Failed): pass

class Request_Refused(Request_Error): pass
class Request_Bad_Version(Request_Refused): pass
class Request_Unknown_Command(Request_Refused): pass
class Request_Unauthorized_Client(Request_Refused): pass
class Request_Invalid_Port(Request_Refused): pass
class Request_Invalid_Format(Request_Refused): pass

class logger:
    def __init__( self, printDebug=False ):
        self._printDebug = printDebug
    
    def parseMsg( self, msg ):
        try:
            msg = ' '.join( [ str(x) for x in list(msg) ] )
            return msg
        except:
            return msg
    
    def info( self, *msg ):
        msg = self.parseMsg( msg )
        msg = '[ ' + now() + ' ][info] ' + msg + '\n'
        sys.stdout.write( msg )
    
    def error( self, *msg ):
        msg = self.parseMsg( msg )
        msg = '[ ' + now() + ' ][error] ' + msg + '\n'
        sys.stderr.write( msg )
    
    def debug( self, *msg ):
        msg = self.parseMsg( msg )
        msg = '[ ' + now() + ' ][debug] ' + msg + '\n'
        if self._printDebug:
            sys.stdout.write( msg )

# Global log object
log = None

def string2port( port_str ):
    """
    This function converts between a packed (16 bits) port number to an
    integer.
    """
    return struct.unpack('>H', port_str)[0]

def port2string( port ):
    """
    This function converts a port number (16 bits integer) into a packed
    string (2 chars).
    """
    return struct.pack('>H', port)
        
# Server class
class w3afAgentClient( threading.Thread ):
    """
    Threading SOCKS4 proxy class.

    Note: this server maintains two lists of all CONNECTION and BIND requests being
    handled. This is not really useful for now but may become in the future.
    Moreover, it has been a good way to learn about the semaphores of the threading
    module :)
    """

    def __init__(self, w3afAgentServer_address='127.0.0.1', w3afAgentServer_port=9092 ):
        """
        Constructor of the server.
        """
        threading.Thread.__init__(self)
        
        # Save the parameters
        self._w3afAgentServer_address = w3afAgentServer_address
        self._w3afAgentServer_port = w3afAgentServer_port
        
        # Remember that we won't use the output manager because this is going to be running
        # on the remote server, and I don't control the om there.
        global log
        log = logger( printDebug=True )
        
        # All that follows is temporary and bogus. We always wait for incoming
        # connections ("bind" requests) on an interface that has a routable IP
        # address. This means no support for multi-homed servers and no way to
        # connect to hosts on local networks.
        # Getting info on the physical interface of the server.
        
        hostname, aliaslist, ipaddrlist = socket.gethostbyname_ex(socket.gethostname())

        # Finding the internet address of the server. If none is found, the first ip is choosed
        
        self.socks_bind_address = None
        for ip in ipaddrlist:
            if is_routable(ip):
                self.socks_bind_address = ip
                break
        if self.socks_bind_address is None:
            self.socks_bind_address = ipaddrlist[0]

        log.info( 'The chosen bind adress is', self.socks_bind_address )
        
    def run( self ):
        # Start the connection manager
        cm = connectionManager( self._w3afAgentServer_address, self._w3afAgentServer_port )
        cm.setBindAddress( self.socks_bind_address )
        cm.start()

class connectionManager( threading.Thread ):
    '''
    This is a service that creates some connections to the remote w3afAgentServer and waits
    for SOCKS requests to arrive on those connections. When a request arrives, I parse the request
    and create a handler instance manage the SOCKS connection.
    '''
    def __init__( self, w3afAgentServer_address, w3afAgentServer_port, connectionPoolLen = 20 ):
        threading.Thread.__init__(self)
        self._connections = []
        self._w3afAgentServer_address = w3afAgentServer_address
        self._w3afAgentServer_port = w3afAgentServer_port
        self._connectionPoolLen = connectionPoolLen
        self.genConnections( connectionPoolLen )
    
    def setBindAddress( self, bindAddy ):
        self._bindAddy = bindAddy
        
    def genConnections( self, number ):
        # Connect to the w3afAgentServer and store the connections in the
        # connection pool
        for i in xrange( number - len(self._connections) ):
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.connect(( self._w3afAgentServer_address , self._w3afAgentServer_port ))
            except Exception, e:
                log.debug('Failed to connect to the w3afAgentServer, exception: ' + str(e) )
                sys.exit(1)
            else:
                self._connections.append( s )
        
    def run( self ):
        while 1:
            # Here I listen for data on all the connections I have and if I get anything I
            # parse the request, after parsing I create a new SocksHandler that will
            # manage all the SOCKS protocol
            ready_to_read, ready_to_write, in_error = select.select(
                self._connections, 
                [], [] )
            
            for sock in in_error:
                self._connections.remove( sock )
            
            for sock in ready_to_read:
                req = self.decode_request( sock.recv( 1024 ) )
                handler = SocksHandler( sock, req )
                handler.setBindAddress( self._bindAddy )
                handler.start()
                self._connections.remove( sock )
                
            self.genConnections( self._connectionPoolLen )
            
    def decode_request(self, data):
        """This function reads the request socket for the request data, decodes
        it and checks that it is well formed.
        """
        # It is useless to process a short request.
        if len(data) < 9: raise Request_Invalid_Format(data)
        
        # Extracting components of the request. Checks are made at each step.
        req = {}

        # SOCKS version of the request.
        req['version']  = ord(data[0])
        if req['version'] != SOCKS_VERSION:
            raise Request_Bad_Version(req)

        # Command used.
        req['command']  = ord(data[1])
        if not req['command'] in COMMANDS:
            raise Request_Unknown_Command(req)

        # Address of the remote peer.
        req['address']  = (
            socket.inet_ntoa(data[4:8]),
            string2port(data[2:4]))
        if not is_port(req['address'][1]):
            raise Request_Invalid_Port(req)
        # Note: only the fact that the port is in [1, 65535] is checked here.
        # Address and port legitimity are later checked in validate_request.

        # Requester user ID. May not be provided.
        req['userid']   = data[8:].strip('\x00')

        # If we are here, then the request is well-formed. Let us return it to
        # the caller.
        return req
        
class SocksHandler( threading.Thread ):
    """This request handler class handles Socks 4 requests."""
    def __init__( self, clientSocket, request ):
        threading.Thread.__init__(self)
        self.clientSocket = clientSocket
        self.request = request
        
    def run( self ):
        self.handle( self.request )
    
    def setBindAddress( self, bindAddy ):
        self._bindAddy = bindAddy
        
    def handle(self, req):
        """
        This function is the main request handler function.

        It delegates each step of the request processing to a different function and
        handles raised exceptions in order to warn the client that its request has
        been rejected (if needed).
        The steps are:
            - decode_request: reads the request and splits it into a dictionary. it checks
              if the request is well-formed (correct socks version, correct command number,
              well-formed port number.
            - validate_request: checks if the current configuration accepts to handle the
              request (client identification, authorization rules)
            - handle_connect: handles CONNECT requests
            - handle_bind: handles BIND requests
        """

        log.debug( thread.get_ident(), '-'*40 )
        log.debug( thread.get_ident(), 'New socks connection request from w3afAgentServer.' )

        try:
            log.debug( thread.get_ident(), 'Decoded request:', req )
            
            # Let's add socks4a support
            self.validate_socks4a(req)
            
            # We are here so the request is valid.
            # We must decide of the action to take according to the "command"
            # part of the request.
            if req['command'] == COMMAND_CONNECT:
                self.handle_connect(req)
            elif req['command'] == COMMAND_BIND:
                self.handle_bind(req)

        # Global SOCKS errors handling.
        except Request_Failed_No_Identd:
            self.answer_rejected(REQUEST_REJECTED_NO_IDENTD)
            log.error( 'Request',thread.get_ident(),'failed, no identd.' )
        except Request_Failed_Ident_failed:
            self.answer_rejected(REQUEST_REJECTED_IDENT_FAILED)
            log.error( 'Request',thread.get_ident(),'failed, ident failed.' )
        except Request_Error:
            self.answer_rejected()
            log.error( 'Request',thread.get_ident(),'failed, invalid request.' )
        except Remote_Connection_Failed:
            self.answer_rejected()
            log.error( 'Remote connection failed while processing request', thread.get_ident() )
        except Bind_TimeOut_Expired:
            self.answer_rejected()
            log.error( 'Bind timeout expired while processing request', thread.get_ident() )
        # Once established, if the remote or the client connection is closed
        # we must exit silently. This exception is in fact the way the function
        # used to forward data between the client and the remote server tells
        # us it has finished working.
        except Connection_Closed:
            pass

    def validate_socks4a( self, req ):
        """This method verifies the extension to socks4 that allows the client
        to send 0.0.0.x as IP address to indicate to the server that it should resolve the hostname
        sent in the ID field and then connect to it.
        """
        ipAddress = req['address'][0]
        if ipAddress.startswith('0.0.0.'):
            if req['userid'] != '':
                # resolve the hostname and reassign the address to the request
                req['address'] = socket.gethostbyname( req['userid'] ), req['address'][1]
            else:
                log.debug('Invalid socks4a request.')
            
        else:
            # this is not a socks4a request
            pass
        
        return req

    def handle_bind(self, req):
        """
        This function handles a BIND request.

        The actions taken are:
        - create a new socket,
        - bind it to the external ip chosen on init of the server,
        - listen for a connection on this socket,
        - register the bind into the server,
        - tell the client the bind is ready,
        - accept an incoming connection,
        - tell the client the connection is established,
        - forward data between the client and the remote peer.
        """
        
        # Create a socket to receive incoming connection.
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # From now on, whatever we do, we must close the "remote" socket before
        # leaving. I love try/finally blocks.
        try:
            # In this block, the only open connection is the client one, so a
            # ERR_CONNECTION_RESET_BY_PEER exception means "exit silently
            # because you won't be able to send me anything anyway".
            # Any other exception must interrupt processing and exit from here.
            try:
                # Binding the new socket to the chosen external ip
                remote.bind((self._bindAddy, 0))
                remote.listen(1)

                # Collecting information about the socket to store it in the
                # "waiting binds" list.
                socket_ip, socket_port = remote.getsockname()
            except socket.error:
                # A "connection reset by peer" here means the client has closed
                # the connection.
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))
                else:
                    # We may be able to make a more precise diagnostic, but
                    # in fact, it doesn't seem useful here for now.
                    raise Remote_Connection_Failed

            # Sending first answer meaning request is accepted and socket
            # is waiting for incoming connection.
            self.answer_granted(socket_ip, socket_port)

            try:
                # Waiting for incoming connection. I use a select here to
                # implement the timeout stuff.
                read_sock, junk, exception_sock = select.select(
                    [remote], [], [remote],
                    120 )
                # If all lists are empty, then the select has ended because
                # of the timer.
                if (read_sock, junk, exception_sock) == ([], [], []):
                    raise Bind_TimeOut_Expired
                # We also drop the connection if an exception condition is
                # detected on the socket. We must also warn the client that
                # its request is rejecte (remember that for a bind, the client
                # expects TWO answers from the proxy).
                if exception_sock:
                    raise Remote_Connection_Failed

                # An incoming connection is pending. Let us accept it
                incoming, peer = remote.accept()
            except:
                # We try to keep a trace of the previous exception
                # for debugging purpose.
                raise Remote_Connection_Failed(sys.exc_info())

            # From now on , we must not forget to close this connection.
            try:
                # We must now check that the incoming connection is from
                # the expected server.
                if peer[0] != req['address'][0]:
                    raise Remote_Connection_Failed_Invalid_Host

                # We can now tell the client the connection is OK, and
                # start the forwarding process.
                self.answer_granted()
                self.forward(self.clientSocket, incoming)
            # Mandatory closing of the socket with the remote peer.
            finally:
                incoming.close()

        # Mandatory closing ofthe listening socket
        finally:
            remote.close()


    def handle_connect(self, req):
        """This function handles a CONNECT request.

        The actions taken are:
            - create a new socket,
            - register the connection into the server,
            - connect to the remote host,
            - tell the client the connection is established,
            - forward data between the client and the remote peer.
        """
        
        # Create a socket to connect to the remote server
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # From now on, we must not forget to close this socket before leaving.
        try:
            try:
                # Connection to the remote server
                log.debug( thread.get_ident(), 'Connecting to', req['address'] )


                # Possible way to handle the timeout defined in the protocol!
                # Make the connect non-blocking, then do a select and keep
                # an eye on the writable socket, just as I did with the
                # accept() from BIND requests.
                # Do this tomorrow... Geez... 00:47... Do this this evening.
                
                remote.connect(req['address'])
                
            # The only connection that can be reset here is the one of the
            # client, so we don't need to answer. Any other socket
            # exception forces us to try to answer to the client.
            except socket.error:
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))
                else:
                    raise Remote_Connection_Failed
            except:
                raise Remote_Connection_Failed
        
            # From now on we will already have answered to the client.
            # Any exception occuring now must make us exit silently.
            try:
                # Telling the client that the connection it asked for is
                # granted.
                self.answer_granted()
                # Starting to relay information between the two peers.
                self.forward(self.clientSocket, remote)
            # We don't have the right to "speak" to the client anymore.
            # So any socket failure means a "connection closed" and silent
            # exit.
            except socket.error:
                raise Connection_Closed
        # Mandatory closing of the remote socket.
        finally:
            remote.close()

    def answer_granted(self, dst_ip = '0.0.0.0', dst_port = 0):
        """This function sends a REQUEST_GRANTED answer to the client."""
        self.answer(REQUEST_GRANTED, dst_ip, dst_port)#!/usr/bin/env python

    def answer_rejected(self, reason = REQUEST_REJECTED_FAILED, dst_ip = '0.0.0.0', dst_port = 0):
        """This function send a REQUEST_REJECTED answer to the client."""
        self.answer(reason, dst_ip, dst_port)

    def answer(self, code = REQUEST_GRANTED, ip_str = '0.0.0.0', port_int = 0):
        """This function sends an answer to the client. This has been
factorised because all answers follow the same format."""

        # Any problem occuring here means that we are unable to "speak" to
        # the client -> we must act as if the connection to it had already
        # been closed.
        try:
            ip    = socket.inet_aton(ip_str)
            port    = port2string(port_int)
            packet  = chr(0)        # Version number is 0 in answer
            packet += chr(code)  # Error code
            packet += port
            packet += ip
            log.debug( thread.get_ident(), 'Sending back:', code, string2port(port), socket.inet_ntoa(ip) )
            self.clientSocket.send(packet)
        except:
            # Trying to keep a trace of the original exception.
            raise Client_Connection_Closed(sys.exc_info())

    def forward(self, client_sock, server_sock):
        """This function makes the forwarding of data by listening to two
sockets, and writing to one everything it reads on the other.

This is done using select(), in order to be able to listen on both sockets
simultaneously and to implement an inactivity timeout."""
        
        # Once we're here, we are not supposed to "speak" with the client
        # anymore. So any error means for us to close the connection.
        log.debug( thread.get_ident(), 'Forwarding.' )
        # These are not used to anything significant now, but I keep them in
        # case I would want to do some statistics/logging.
        octets_in, octets_out = 0, 0
        try:
            try:
                # Here are the sockets we will be listening.
                sockslist = [client_sock, server_sock]
                while 1:
                    # Let us listen...
                    readables, writeables, exceptions = select.select(
                        sockslist, [], [],
                        360 )
                    # If the "exceptions" list is not empty or if we are here
                    # because of the timer (i.e. all lists are empty), then
                    # we must must bail out, we have finished our work.
                    if (exceptions
                        or (readables, writeables, exceptions) == ([], [], [])):
                        raise Connection_Closed

                    # Only a precaution.                    
                    data = ''

                    # Just in case we would be in the improbable case of data
                    # awaiting to be read on both sockets, we treat the
                    # "readables" list as if it oculd contain more than one
                    # element. Thus the "for" loop...
                    for readable_sock in readables:
                        # We know the socket we want to read of, but we still
                        # must find what is the other socket. This method
                        # builds a list containing one element.
                        writeableslist = [client_sock, server_sock]
                        writeableslist.remove(readable_sock)

                        # We read one chunk of data and then send it to the
                        # other socket
                        data = readable_sock.recv( 1024 )
                        # We must handle the case where data=='' because of a
                        # bug: we sometimes end with an half-closed socket,
                        # i.e. a socket closed by the peer, on which one can
                        # always read, but where there is no data to read.
                        # This must be detected or it would lead to an infinite
                        # loop.
                        if data:
                            writeableslist[0].send(data)
                            # This is only for future logging/stats.
                            if readable_sock == client_sock:
                                octets_out += len(data)
                            else:
                                octets_in += len(data)
                        else:
                            # The sock is readable but nothing can be read.
                            # This means a poorly detected connection close.
                            raise Connection_Closed
            # If one peer closes its conenction, we have finished our work.
            except socket.error:
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Connection_Closed
                raise
        finally:
            log.debug( thread.get_ident(), octets_in, 'octets in and', octets_out, 'octets out. Connection closed.' )


if __name__ == "__main__":
    addr = sys.argv[1]
    port = int(sys.argv[2])
    w3 = w3afAgentClient( w3afAgentServer_address=addr, w3afAgentServer_port=port )
    w3.start()
    
