"""
extrusionClient.py

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

import socket
import sys


class extrusionClient:
    """
    This class defines a simple client, that connects to every port that is passed to it
    in the constructor and closes the connection afterwards.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, host, tcpPorts, udpPorts):
        self._host = host
        self._tcpPorts = tcpPorts
        self._udpPorts = udpPorts

    def start(self):
        """
        Performs the connections.
        """
        def conn(sock, host, port):
            try:
                sock.connect((host, port))
                sock.close()
            except:
                pass

        for port in self._tcpPorts:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn(s, self._host, int(port))

        for port in self._udpPorts:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.sendto('', (self._host, int(port)))
            except:
                pass

if __name__ == "__main__":
    # do the work
    try:
        ipAddress = sys.argv[1]
        tcpPorts = sys.argv[2].split(',')
        udpPorts = sys.argv[3].split(',')
    except:
        print 'Bad parameters.'
    else:
        ec = extrusionClient(ipAddress, tcpPorts, udpPorts)
        ec.start()
        print 'OK.'
