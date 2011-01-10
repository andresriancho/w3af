'''
w3afAgentServer.py

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

if __name__ == '__main__':
    import sys
    import os
    sys.path.append( os.getcwd() )
    

import core.controllers.outputManager as om
from core.controllers.threads.w3afThread import w3afThread
from core.controllers.w3afException import w3afException
import core.data.kb.config as cf

import sys
from socket import *
from threading import Thread
import threading
import time


class connectionManager( w3afThread ):
    '''
    This is a service that listens on some port and waits for the w3afAgentClient to connect.
    It keeps the connections alive so they can be used by a tcprelay object in order to relay
    the data between the w3afAgentServer and the w3afAgentClient.
    '''
    def __init__( self, ip_address, port ):
        w3afThread.__init__(self)
        
        #    Configuration
        self._ip_address = ip_address
        self._port = port
        
        #    Internal
        self._connections = []
        self._cmLock = threading.RLock()
    
        self._keepRunning = True
        self._reportedConnection = False
    
    def stop( self ):
        self._keepRunning = False
        s = socket( AF_INET, SOCK_STREAM )
        try:
            s.connect( (self._ip_address , self._port) )
            s.close()
        except:
            pass
        
        for conn in self._connections:
            conn.close()
        om.out.debug('Stoped connection manager.')
    
    def run( self ):
        '''
        Thread entry point.
        
        @return: None
        '''
        
        #    Start listening
        try:
            self.sock = socket( AF_INET, SOCK_STREAM )
            self.sock.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
            self.sock.bind( (self._ip_address , self._port ) )
            self.sock.listen(5)
        except Exception, e:
            msg = '[w3afAgentServer] Failed to bind to %s:%s' % (self._ip_address , self._port)
            msg += '. Error: "%s".' % e
            raise w3afException( msg )
            
        # loop !
        while self._keepRunning:
            try:
                newsock, address = self.sock.accept()
            except KeyboardInterrupt, k:
                om.out.console('Exiting.')
            except error:
                # This catches socket timeouts
                pass
            else:
                om.out.debug( '[connectionManager] Adding a new connection to the connection manager.' )
                self._connections.append( newsock )
                if not self._reportedConnection:
                    self._reportedConnection = True
                    om.out.console( 'w3afAgent service is up and running.' )
    
    def isWorking( self ):
        '''
        @return: Did the remote agent connected to me ?
        '''
        return self._reportedConnection
    
    def getConnection( self ):
        
        if self._connections:
            self._cmLock.acquire()
            
            res = self._connections[ 0 ]
            self._connections = self._connections[1:]
            
            self._cmLock.release()
            return res
        else:
            raise w3afException('[connectionManager] No available connections.')
            
            
class PipeThread( w3afThread ):
    pipes = []
    def __init__( self, source, sink ):
        w3afThread.__init__(self)
        self.source = source
        self.sink = sink
        
        om.out.debug('[PipeThread] Starting data forwarding: %s ( %s -> %s )' % ( self, source.getpeername(), sink.getpeername() ))
        
        PipeThread.pipes.append( self )
        om.out.debug('[PipeThread] Active forwardings: %s' % len(PipeThread.pipes) )
        
        self._keepRunning = True

    def stop( self ):
        self._keepRunning = False
        try:
            self.source.close()
            self.sink.close()
        except:
            pass
        
    def run( self ):
        while self._keepRunning:
            try:
                data = self.source.recv( 1024 )
                if not data: break
                self.sink.send( data )
            except:
                break

        PipeThread.pipes.remove( self )
        om.out.debug('[PipeThread] Terminated one connection, active forwardings: %s' % len(PipeThread.pipes) )
        
class tcprelay( w3afThread ):
    def __init__( self, ip_address, port, cm ):
        w3afThread.__init__(self)
        # save the connection manager
        self._cm = cm
        self._ip_address = ip_address
        self._port = port
        
        # Listen and handle socks clients
        self.sock = socket( AF_INET, SOCK_STREAM )
        self.sock.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(( self._ip_address , self._port ))
        except:
            raise w3afException('Port ('+ self._ip_address + ':' + str(self._port)+') already in use.' )
        else:
            om.out.debug('[tcprelay] Bound to ' + self._ip_address + ':' + str(self._port) )
            
            self.sock.listen(5)
        
            self._keepRunning = True
            self._pipes = []
    
    def stop( self ):
        self._keepRunning = False
        s = socket( AF_INET, SOCK_STREAM )
        s.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            s.connect( ('localhost', self._port) )
            s.close()
        except:
            pass

        
        for pipe in self._pipes:
            pipe.stop()
        
        om.out.debug('[tcprelay] Stopped tcprelay.')
        
    def run( self ):
        while self._keepRunning:
            try:
                sockClient, address = self.sock.accept()
            except error:
                # This catches socket timeouts
                pass
            else:
                om.out.debug('[tcprelay] New socks client connection.')
                
                # Get an active connection from the connection manager and start forwarding data
                try:
                    connToW3afClient = self._cm.getConnection()
                except KeyboardInterrupt, k:
                    om.out.information('Exiting.')
                except:
                    om.out.debug('[tcprelay] Connection manager has no active connections.')
                else:
                    pt1 = PipeThread( sockClient, connToW3afClient )
                    self._pipes.append( pt1 )
                    pt1.start()
                    pt2 = PipeThread( connToW3afClient, sockClient )
                    self._pipes.append( pt2 )
                    pt2.start()
            

class w3afAgentServer( w3afThread ):
    def __init__( self, ip_address, socks_port=1080, listen_port=9092 ):
        w3afThread.__init__(self)
        
        #    Configuration
        self._ip_address = ip_address
        self._listen_port = listen_port
        self._socks_port = socks_port
        
        #    Internal
        self._isRunning = False
        self._error = ''
        
    def run( self ):
        '''
        Entry point for the thread.
        '''
        try:
            self._cm = connectionManager( self._ip_address, self._listen_port )
            self._cm.start()
        except w3afException, w3:
            self._error = 'Failed to start connection manager inside w3afAgentServer, exception: ' + str(w3)
        else:
            try:
                self._tcprelay = tcprelay( self._ip_address, self._socks_port, self._cm )
                self._tcprelay.start()
            except w3afException, w3:
                self._error = 'Failed to start tcprelay inside w3afAgentServer, exception: "%s"' % w3
                self._cm.stop()
            else:
                self._isRunning = True
        
    def stop( self ):
        if self._isRunning:
            om.out.debug('Stopping w3afAgentServer.')
            self._cm.stop()
            self._tcprelay.stop()
        else:
            om.out.debug('w3afAgentServer is not running, no need to stop it.')
    
    def getError( self ):
        return self._error
    
    def isRunning( self ):
        return self._isRunning
        
    def isWorking( self ):
        return self._cm.isWorking()
    
if __name__ == '__main__':
    sys.path.append('../../../../')
    
    if len(sys.argv) != 3:
        print
        print 'w3afAgent usage:'
        print 'python w3afAgentServer.py <bind-address> <bind-port>'
        print
        sys.exit(-1)
        
    ip_address = sys.argv[1]
    agent = w3afAgentServer( ip_address, listen_port=int(sys.argv[2]) )
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print 'bye.'
