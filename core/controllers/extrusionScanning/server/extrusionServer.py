'''
extrusionServer.py

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

import socket
from core.controllers.w3afException import w3afException

from scapy.all import sniff
from scapy.all import get_if_addr
from scapy.all import IP
from scapy.all import TCP
from scapy.all import UDP
            
import core.controllers.outputManager as om
import core.data.kb.config as cf


class extrusionServer:
    '''
    This class defines a simple server that listens on the current interface for connections
    made from the extrusionClient.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self, tcpPortList, udpPortList , host=None, iface=None ):
        '''
        If you don't know whats the IP address used by the remote host ( the one thats running the extrusionClient )
        you can just say None and the extrusionServer will try to figure it out.
        
        @parameter host: The host from where we expect the connections
        @parameter portList: The portList ( as passed to extrusionClient ) to listen for        
        @parameter iface: The interface where scapy is going to listen for packets
        '''
        self._host = host
        self._udpPortList = udpPortList
        self._tcpPortList = tcpPortList
        
        if iface:
            self._iface = iface
        else:
            self._iface = cf.cf.getData( 'interface' )
    
    def canSniff( self ):
        '''
        Determine if the user running w3af can sniff packets on the configured interface.
        '''
        try:
            p = sniff(filter='port 53', iface=self._iface, timeout=1 )
        except Exception:
            return False
        else:
            return True
            
    def sniffAndAnalyze( self ):
        '''
        Performs the sniffing
        '''
        # Create the filter
        allPorts = self._tcpPortList[:]
        allPorts.extend( self._udpPortList )
        filter = ' or '.join( [ 'port ' + str(p) for p in allPorts ] )
        
        om.out.information('ExtrusionServer listening on interface: ' + self._iface )
        try:
            pList = sniff(filter=filter, iface=self._iface, timeout=5 )
        except socket.error , e:
            self._res = []
            msg = 'Failed to sniff on interface: ' + self._iface + '. Hints: Are you root? Does this interface exist?'
            om.out.error( msg )
            raise w3afException( msg )
        else:
            if pList:
                om.out.debug('Analyzing packetlist captured by scapy. The packetlist is:')
                for p in pList:
                    om.out.debug( str(p.summary()) )
            else:
                om.out.debug('No packets captured by scapy.')
                self._res = []
                return self._res
                
            self._res = self._analyzePackets( pList )
            return self._res
    
    def getResult( self ):
        return self._res
    
    def _analyzePackets( self, packetList ):
        '''
        Analyze the packets and return a list of ports that can be used by the remote host
        to connect back to the extrusionServer.
        '''
        
        if self._host is None:
            # This is hard to do...
            possiblePackets = []
            possibleHosts = {}
            goodPorts = []
            goodHosts = []
            
            for p in packetList:
                # Analyze TCP
                if p[TCP] is not None and p[TCP].dport in self._tcpPortList and p[IP].dst in get_if_addr( self._iface )\
                and p[TCP].flags == 0x2: # is SYN
                    possiblePackets.append( p )
                    if p[IP].src in possibleHosts:
                        possibleHosts[ p[IP].src ] += 1
                    else:
                        possibleHosts[ p[IP].src ] = 1
                
                # Analyze UDP
                if p[UDP] is not None and p[UDP].dport in self._udpPortList and p[IP].dst in get_if_addr( self._iface ):
                    possiblePackets.append( p )
                    if p[IP].src in possibleHosts:
                        possibleHosts[ p[IP].src ] += 1
                    else:
                        possibleHosts[ p[IP].src ] = 1
            
            for p in possiblePackets:
                om.out.debug('[extrusionServer] Possible packet: ' + p.summary() )
                
            # Now get the one that has more probability of being the one... and report the list of ports
            def sortfunc(x,y):
                return cmp(x[1],y[1])
            items = possibleHosts.items()
            items.sort(sortfunc)
            
            # Now I report the ports for the hosts with more connections
            i = 0
            while i < len(items) and items[0][1] == items[i][1]:
                goodHosts.append( items[i][0] )
                i += 1
            
            for p in possiblePackets:
                if p[IP].src in goodHosts:
                    if p[TCP] is not None:
                        tuple = ( p[IP].src , p[TCP].dport, 'TCP' )
                        if tuple not in goodPorts:
                            goodPorts.append( tuple )
                            om.out.debug('[extrusionServer] Adding ' + str(tuple) )
                    
                    if p[UDP] is not None:
                        tuple = ( p[IP].src , p[UDP].dport, 'UDP' )
                        if tuple not in goodPorts:
                            goodPorts.append( tuple )
                            om.out.debug('[extrusionServer] Adding ' + str(tuple) )
                        
            return goodPorts
            
        else:
            goodPorts = []
            for p in packetList:
                if p[TCP] is not None and p[TCP].dport in self._tcpPortList and p[IP].src == self._host \
                and p[TCP].flags == 0x2:
                    
                    if ( p[IP].src , p[TCP].dport, 'TCP') not in goodPorts:
                        goodPorts.append( ( p[IP].src , p[TCP].dport, 'TCP') )
                
                if p[UDP] is not None and p[UDP].dport in self._udpPortList and p[IP].src == self._host:

                    if ( p[IP].src , p[UDP].dport, 'UDP') not in goodPorts:
                        goodPorts.append( ( p[IP].src , p[UDP].dport, 'UDP') )
                        
            return goodPorts
        
if __name__ == "__main__":
    # do the work
    ec = extrusionServer( [80,25,1433], iface='lo' )
    ec.sniffAndAnalyze()
    print ec.getResult()
    
