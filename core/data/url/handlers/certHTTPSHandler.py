'''
certHTTPSHandler.py

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

import urllib2
import httplib
import core.controllers.outputManager as om

class certHTTPSConnection( httplib.HTTPSConnection ):
    '''
    An HTTPSConnection abstraction for easy integration with urllib2.
    '''
    key_file = None
    cert_file = None
    
    def __init__( self, host, port=None, strict=None ):
        httplib.HTTPSConnection.__init__( self, host, port, self.key_file, self.cert_file, strict)
        #om.out.debug('Called __init__ of certHTTPSConnection.')

class certHTTPSHandler( urllib2.HTTPSHandler ):
    '''
    An https handler for urllib2 that knows what to do with cert and key files.
    '''
    def __init__( self, debuglevel = 0 ):
        urllib2.HTTPSHandler.__init__( self, debuglevel )
        self._sslCertFile = None
        self._sslKeyFile = None
        om.out.debug('Called __init__ of certHTTPSHandler.')
        
    def getSSLKeyFile( self ):
        '''
        @return: A string with the SSL key path and filename.
        '''
        return self._sslKeyFile
        
    def setSSLKeyFile( self, keyFile ):
        '''
        @parameter keyFile: A string with the SSL key path and filename.
        @return: None
        ''' 
        self._sslKeyFile = keyFile
        
    def getSSLCertFile( self ):
        '''
        @return: A string with the SSL cert path and filename.
        '''
        return self._sslCertFile
        
    def setSSLCertFile( self, file ):
        '''
        @parameter file: A string with the SSL cert path and filename.
        @return: None
        '''     
        self._sslCertFile = file
        
    def https_open(self, req):
        # Original
        #return self.do_open(httplib.HTTPSConnection, req)
        
        # My version :P
        certHTTPSConnection.cert_file = self.getSSLCertFile()
        certHTTPSConnection.key_file = self.getSSLKeyFile()
        return self.do_open(certHTTPSConnection, req)

