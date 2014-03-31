"""
AESSocket.py

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

"""
msg = "Nothing in this file is used in w3af. This was a test that was truncated by my personal\
lack of interest in using encryption here, my lack of time and the main reason: I'm lazy ;)\
Also, pyrijndael was only used here, so I removed the dependency, which was a problem for debian."
raise Exception(msg)


# If I wan't to continue to develop AESSocket, I should re-install pyrijndael.
from pyrijndael.pyRijndael import DecryptData
from pyrijndael.pyRijndael import EncryptData

def makeAESSocket( key , sock ):
    '''
    :param key: A string that will be the key for AES algorithm
    :param sock: python socket
    :return: a socket that will encrypt / decrypt all data that it sends and receives
    '''
    sock._original_recv = sock.recv
    sock._original_send = sock.send
    sock._key = key

    def aes_recv( self, length ):
        crypt_data = self._original_recv( length )
        data = DecryptData( self._key, crypt_data )
        return data

    def aes_send( self, data ):
        crypt_data = EncryptData( self._key, data )
        sentBytes = self._original_send( crypt_data )
        if sentBytes == len( crypt_data ):
            return len(data)
        else:
            # Just to say "not all data was transfered"
            return len(data) - 1

    sock.recv = aes_recv
    sock.send = aes_send

    return sock
"""
