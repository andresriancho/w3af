"""
w3afAgentServer.py

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
import sys
import os
import socket
import threading

from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException


class ConnectionManager(Process):
    """
    This is a service that listens on some port and waits for the w3afAgentClient
    to connect. It keeps the connections alive so they can be used by a TCPRelay
    object in order to relay the data between the w3afAgentServer and the
    w3afAgentClient.
    """
    def __init__(self, ip_address, port):
        Process.__init__(self)
        self.daemon = True

        #    Configuration
        self._ip_address = ip_address
        self._port = port

        #    Internal
        self._connections = []
        self._cmLock = threading.RLock()

        self._keep_running = True
        self._reportedConnection = False

    def stop(self):
        self._keep_running = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self._ip_address, self._port))
            s.close()
        except:
            pass

        for conn in self._connections:
            conn.close()
        om.out.debug('Stoped connection manager.')

    def run(self):
        """
        Thread entry point.

        :return: None
        """

        #    Start listening
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self._ip_address, self._port))
            self.sock.listen(5)
        except Exception, e:
            msg = '[w3afAgentServer] Failed to bind to %s:%s' % (
                self._ip_address, self._port)
            msg += '. Error: "%s".' % e
            raise BaseFrameworkException(msg)

        # loop !
        while self._keep_running:
            try:
                newsock, address = self.sock.accept()
            except KeyboardInterrupt, k:
                om.out.console('Exiting.')
                break
            except socket.error:
                # This catches socket timeouts
                pass
            else:
                om.out.debug('[ConnectionManager] Adding a new connection to the connection manager.')
                self._connections.append(newsock)
                if not self._reportedConnection:
                    self._reportedConnection = True
                    om.out.console('w3afAgent service is up and running.')

    def is_working(self):
        """
        :return: Did the remote agent connected to me ?
        """
        return self._reportedConnection

    def get_connection(self):

        if self._connections:
            self._cmLock.acquire()

            res = self._connections[0]
            self._connections = self._connections[1:]

            self._cmLock.release()
            return res
        else:
            raise BaseFrameworkException(
                '[ConnectionManager] No available connections.')


class PipeThread(Process):
    pipes = []

    def __init__(self, source, sink):
        Process.__init__(self)
        self.daemon = True

        self.source = source
        self.sink = sink

        om.out.debug('[PipeThread] Starting data forwarding: %s ( %s -> %s )' %
                     (self, source.getpeername(), sink.getpeername()))

        PipeThread.pipes.append(self)
        om.out.debug(
            '[PipeThread] Active forwardings: %s' % len(PipeThread.pipes))

        self._keep_running = True

    def stop(self):
        self._keep_running = False
        try:
            self.source.close()
            self.sink.close()
        except:
            pass

    def run(self):
        while self._keep_running:
            try:
                data = self.source.recv(1024)
                if not data:
                    break
                self.sink.send(data)
            except:
                break

        PipeThread.pipes.remove(self)
        om.out.debug('[PipeThread] Terminated one connection, active forwardings: %s' % len(PipeThread.pipes))


class TCPRelay(Process):
    def __init__(self, ip_address, port, cm):
        Process.__init__(self)
        self.daemon = True

        # save the connection manager
        self._cm = cm
        self._ip_address = ip_address
        self._port = port

        # Listen and handle socks clients
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.sock.bind((self._ip_address, self._port))
        except:
            raise BaseFrameworkException('Port (' + self._ip_address +
                                ':' + str(self._port) + ') already in use.')
        else:
            om.out.debug('[TCPRelay] Bound to ' +
                         self._ip_address + ':' + str(self._port))

            self.sock.listen(5)

            self._keep_running = True
            self._pipes = []

    def stop(self):
        self._keep_running = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect(('localhost', self._port))
            s.close()
        except:
            pass

        for pipe in self._pipes:
            pipe.stop()

        om.out.debug('[TCPRelay] Stopped TCPRelay.')

    def run(self):
        while self._keep_running:
            try:
                sock_cli, address = self.sock.accept()
            except socket.error:
                # This catches socket timeouts
                pass
            else:
                om.out.debug('[TCPRelay] New socks client connection.')

                # Get an active connection from the connection manager and start forwarding data
                try:
                    connToW3afClient = self._cm.get_connection()
                except KeyboardInterrupt:
                    om.out.information('Exiting.')
                    break
                except:
                    om.out.debug('[TCPRelay] Connection manager has no active connections.')
                else:
                    pt1 = PipeThread(sock_cli, connToW3afClient)
                    self._pipes.append(pt1)
                    pt1.start()
                    pt2 = PipeThread(connToW3afClient, sock_cli)
                    self._pipes.append(pt2)
                    pt2.start()


class w3afAgentServer(Process):
    def __init__(self, ip_address, socks_port=1080, listen_port=9092):
        Process.__init__(self)
        self.daemon = True

        #    Configuration
        self._ip_address = ip_address
        self._listen_port = listen_port
        self._socks_port = socks_port

        #    Internal
        self._is_running = False
        self._error = ''

    def run(self):
        """
        Entry point for the thread.
        """
        try:
            self._cm = ConnectionManager(self._ip_address, self._listen_port)
            self._cm.start()
        except BaseFrameworkException, w3:
            self._error = 'Failed to start connection manager inside w3afAgentServer, exception: ' + str(w3)
        else:
            try:
                self._TCPRelay = TCPRelay(
                    self._ip_address, self._socks_port, self._cm)
                self._TCPRelay.start()
            except BaseFrameworkException, w3:
                self._error = 'Failed to start TCPRelay inside w3afAgentServer, exception: "%s"' % w3
                self._cm.stop()
            else:
                self._is_running = True

    def stop(self):
        if self._is_running:
            om.out.debug('Stopping w3afAgentServer.')
            self._cm.stop()
            self._TCPRelay.stop()
        else:
            om.out.debug('w3afAgentServer is not running, no need to stop it.')

    def get_error(self):
        return self._error

    def is_running(self):
        return self._is_running

    def is_working(self):
        return self._cm.is_working()

if __name__ == '__main__':
    sys.path.append(os.getcwd())
    sys.path.append('../../../../')

    if len(sys.argv) != 3:
        print
        print 'w3afAgent usage:'
        print 'python w3afAgentServer.py <bind-address> <bind-port>'
        print
        sys.exit(-1)

    ip_address = sys.argv[1]
    agent = w3afAgentServer(ip_address, listen_port=int(sys.argv[2]))

    try:
        agent.run()
    except KeyboardInterrupt:
        print 'bye.'
