'''
basePayloadTransfer.py

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

import hashlib


class basePayloadTransfer:
    '''
    This is a base class for doing payload transfers.
    '''

    def __init__( self , execMethod, os ):
        self._exec_method = execMethod
        self._os = os
        
    def canTransfer( self ):
        '''
        This method is used to test if the transfer method works as expected. Usually the implementation of
        this should transfer 10 bytes and check if they arrived as expected to the other end.
        '''
        raise w3afException('You should implement the canTransfer method when you inherit from basePayloadTransfer.')
    
    def estimateTransferTime( self, size ):
        '''
        @return: An estimated transfer time for a file with the specified size.
        '''
        raise w3afException('You should implement the estimateTransferTime method when you inherit from basePayloadTransfer.')
        
    def transfer( self, strObject, destination ):
        '''
        This method is used to transfer the strObject from w3af to the compromised server,
        '''
        raise w3afException('You should implement the transfer method when you inherit from basePayloadTransfer.')
    
    def getSpeed( self ):
        '''
        @return: The transfer speed of the transfer object. It should return a number between 100 (fast) and 1 (slow)
        '''
        raise w3afException('You should implement the getSpeed method when you inherit from echo.')

    def verify_upload(self, file_content, remote_filename):
        '''
        Runs a series of commands to verify if the file was successfully uploaded.
        
        @param file_content: The bytestream that should be in the remote_filename
        @param remote_filename: The remote file where the uploaded content should be in
        @return: True if the file was successfully uploaded.
        '''
        if '/etc/passwd' in self._exec_method( 'md5sum /etc/passwd' ): 
            md5sum_res = self._exec_method( 'md5sum ' + remote_filename )
            hash = md5sum_res.split(' ')[0]
            
            m = hashlib.md5()
            m.update(file_content)
            return hash == m.hexdigest()
    
        #    TODO: Hmmmmmmm....
        return True