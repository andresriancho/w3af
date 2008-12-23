'''
sslCertificate.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.parsers.urlParser import getProtocol, getNetLocation

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from OpenSSL import SSL, crypto
import socket
import select


class sslCertificate(baseAuditPlugin):
    '''
    Check the SSL certificate validity( if https is being used ).
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def audit(self, freq ):
        '''
        Get the cert and do some checks against it.
        
        @param freq: A fuzzableRequest
        '''
        url = freq.getURL()
        if 'HTTPS' == getProtocol( url ).upper():
            # Parse the domain:port
            splited = getNetLocation(url).split(':')
            if len( splited ) == 1:
                port = 443
                host = splited[0]
            else:
                port = int(splited[1])
                host = splited[0]

            # Create the connection
            socket_obj = socket.socket()            
            try:
                socket_obj.connect( ( host , port ) )
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ssl_conn = SSL.Connection(ctx, socket_obj)

                # Go to client mode
                ssl_conn.set_connect_state()
                
                # If I don't send something here, the "get_peer_certificate"
                # method returns None. Don't ask me why!
                #ssl_conn.send('GET / HTTP/1.1\r\n\r\n')
                self.ssl_wrapper( ssl_conn, ssl_conn.send, ('GET / HTTP/1.1\r\n\r\n', ), {})
            except Exception, e:
                om.out.error('Error in audit.sslCertificate: "' + repr(e)  +'".')
            else:
                # Get the cert
                cert = ssl_conn.get_peer_certificate()
                
                # Perform the analysis
                self._analyze_cert( cert, ssl_conn )
                
                # Print the SSL information to the log
                desc = 'This is the information about the SSL certificate used in the target site:'
                desc += '\n'
                desc += self._dump_X509(cert)
                om.out.information( desc )
                i = info.info()
                i.setName('SSL Certificate' )
                i.setDesc( desc )
                kb.kb.append( self, 'certificate', i )

    def ssl_wrapper(self, ssl_obj, method, args, kwargs):
        '''
        This is a method that calls SSL functions, wrapping them around
        try/except and handling WantRead and WantWrite errors.
        '''
        while True:
            try:
                return apply( method, args, kwargs )
                break
            except SSL.WantReadError:
                select.select([ssl_obj],[],[],10.0)
            except SSL.WantWriteError:
                select.select([],[ssl_obj],[],10.0)

    def _analyze_cert(self, cert, ssl_conn):
        '''
        Analyze the cert.
        
        @parameter cert: The cert object from pyopenssl.
        @parameter ssl_conn: The SSL connection.
        '''
        server_digest_SHA1 = cert.digest('sha1')
        server_digest_MD5 = cert.digest('md5')

        # Check for expired
        if cert.has_expired():
            i = info.info()
            i.setName('Expired SSL certificate' )
            i.setDesc( 'The certificate with MD5 digest: "' + server_digest_MD5 + '" has expired.' )
            kb.kb.append( self, 'expired', i )
            
        if cert.get_version() < 2: 
            i = info.info()
            i.setName('Insecure SSL version' )
            desc = 'The certificate is using an old version of SSL (' + str(cert.get_version())
            desc += '), which is insecure.'
            i.setDesc( desc )
            kb.kb.append( self, 'version', i )

        peer = cert.get_subject()
        issuer = cert.get_issuer()
        ciphers = ssl_conn.get_cipher_list()

    def _dump_X509(self, cert):
        '''
        Dump X509
        '''
        res = ''
        res += "- Digest (SHA-1): " + cert.digest("sha1") +'\n'
        res += "- Digest (MD5): " + cert.digest("md5") +'\n'
        res += "- Serial#: " + str(cert.get_serial_number()) +'\n'
        res += "- Version: " + str(cert.get_version()) +'\n'

        expired = cert.has_expired() and "Yes" or "No"
        res += "- Expired: " + expired + '\n'
        res += "- Subject: " + str(cert.get_subject()) + '\n'
        res += "- Issuer: " + str(cert.get_issuer()) + '\n'
        
        # Dump public key
        pkey = cert.get_pubkey()
        typedict = {crypto.TYPE_RSA: "RSA", crypto.TYPE_DSA: "DSA"}
        res += "- PKey bits: " + str(pkey.bits()) +'\n'
        res += "- PKey type: %s (%d)" % (typedict.get(pkey.type(), "Unknown"), pkey.type()) +'\n'
        
        res += '- Certificate dump: \n' + crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
        
        # Indent
        res = res.replace('\n', '\n    ')
        res = '    ' + res
        
        return res

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin audits SSL certificate parameters.
        
        Note: It's only usefull when testing HTTPS sites.
        '''
