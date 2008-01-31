'''
agentManager.py

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
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
import socket

class agentManager:
    '''
    This class defines a manager for w3af agents.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self ):
        # Internal variables
        self._counter = 0
        self._requests = []
        
        # User configured variables
        self._host = '0.0.0.0'
        self._port = 12345
        
    def start( self ):
        serversocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        serversocket.bind(( self._host , self._port ))
        serversocket.listen(5)
        
        while 1:
            #accept connections from outside
            (clientsocket, address) = serversocket.accept()
            
            # do SSL
            #ssl_sock = socket.ssl( clientsocket )
            ssl_sock = clientsocket
            
            # handle the agent
            self._handleAgent(ssl_sock)
            
    def _handleAgent( self, clientsocket ):
        '''
        This method handles an agent that is connecting to this agentManager.
        
        @parameter clientsocket: A socket where the client is connected
        @return: None
        '''
        ar = self._requests.pop()
        
        recv = clientsocket.recv( len('<ready/>') )
        
        self._counter += 1
        xml = ar.toString(self._counter)
        clientsocket.send( xml )
        om.out.information( 'Sending: ' + xml )
        
        recv = ''
        while True:
            readChars = clientsocket.recv( 10 )
            om.out.information( 'Received: ' + readChars )
            if recv.count('</call>'):
                break
                om.out.information('End of response found.')
        om.out.information( 'Received: ' + recv )
        
    def addRequestToQueue( self, request ):
        '''
        The agentManager has a queue, where it stores the requests made by the
        framework and then sends them to the agents one by one.
        '''
        self._requests.append( request )


class agentRequest:
    def __init__( self, command, parameterMap ):
        self._command = command
        self._parameterMap = parameterMap
        
    def toString( self, id ):
        '''
        <call>
            <command>system</command>
            <id>5812</id>
            <parameterList>
                <param name="run" >ls</param>
            </parameterList>
        </call>
        '''
        res = '<call>\n'
        res += '\t<command>%s</command>\n' % self._command
        res += '\t<id>%i</id>\n' % id
        res += '\t<parameterList>\n'
        for name, value in self._parameterMap.items():
                res += '\t\t<param name="%s" >%s</param>\n' % (name, value)
        res += '\t</parameterList>\n'
        res += '</call>'
        return res
        
