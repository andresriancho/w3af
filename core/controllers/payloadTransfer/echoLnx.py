'''
echoLnx.py

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
from core.controllers.payloadTransfer.basePayloadTransfer import basePayloadTransfer as basePayloadTransfer

import time


class echoLnx( basePayloadTransfer ):
    '''
    This is a class that defines how to send a file to a remote server using the "echo" command.
    '''

    def __init__( self , exec_method, os ):
        self._exec_method = exec_method
        self._os = os
        
        # internal configuration parameters
        self._step = 30
        
    def canTransfer( self ):
        '''
        This method is used to test if the transfer method works as expected. The implementation of
        this should transfer 10 bytes and check if they arrived as expected to the other end.
        '''
        # Check if echo exists and works as expected
        res = self._exec_method( "/bin/echo -n 'w3af'" )
        if 'w3af' != res:
            om.out.debug('Remote server returned: "'+res+'" when expecting "w3af".')
            return False
        else:
            return True
    
    def estimateTransferTime( self, size ):
        '''
        @return: An estimated transfer time for a file with the specified size.
        '''
        before = time.time()
        res = self._exec_method( "echo w3af" )
        after = time.time()
        
        # Estimate the time...
        numberOfRequests = size / self._step
        requestTime = after - before
        timeTaken = round( requestTime * numberOfRequests )
        
        om.out.debug('The file transfer will take "' + str(timeTaken) +'" seconds.')
        return int(timeTaken)
        
    def transfer( self, strObject, destination ):
        '''
        This method is used to transfer the strObject from w3af to the compromised server.
        '''
        self._filename = destination
        
        # Zeroing destination file
        self._exec_method( '> ' + self._filename )
        
        i = 0
        while i < len( strObject ):
            # Prepare the command
            cmd = "/bin/echo -ne "
            for c in strObject[i:i+self._step]:
                cmd += '\\\\' + oct( ord( c ) ).zfill(4)
            
            cmd += " >> " + self._filename
            i += self._step
            
            # Send the command to the remote server
            self._exec_method( cmd )
                    
        return self.verify_upload( strObject, self._filename ) 
        
    def getSpeed( self ):
        '''
        @return: The transfer speed of the transfer object. It should return a number between 100 (fast) and 1 (slow)
        '''
        return 1
        
