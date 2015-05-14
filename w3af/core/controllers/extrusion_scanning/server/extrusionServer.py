"""
extrusionServer.py

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
import socket
import time

from w3af.core.controllers.exceptions import BaseFrameworkException

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf


class extrusionServer(object):
    """
    This class defines a simple server that listens on the current interface
    for connections made from the extrusionClient.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, tcp_ports, udp_ports, host=None, iface=None):
        """
        If you don't know what the IP address used by the remote host is
        (the one that's running the extrusionClient) you can just say None
        and the extrusionServer will try to figure it out.

        :param host: The host from where we expect the connections
        :param tcp_ports: The TCP ports as passed to extrusionClient to listen
        :param udp_ports: The UDP ports as passed to extrusionClient to listen
        :param iface: The interface where scapy is going to listen for packets
        """
        self._host = host
        self._udp_ports = udp_ports
        self._tcp_ports = tcp_ports
        self._sniffing = False
        self.reverse_ports_allowed = []

        if iface is not None:
            self._iface = iface
        else:
            cf_iface = cf.cf.get('interface')
            if cf_iface is not None:
                self._iface = cf_iface
            else:
                msg = 'Failed to bind extrusionServer to an interface.'
                raise Exception(msg)

    def can_sniff(self):
        """
        Determine if the user running w3af can sniff packets on the configured
        interface.
        """
        # Import things from scapy when I need them in order to reduce memory
        # usage (which is specially big in scapy module, just when importing)
        from scapy.all import sniff

        try:
            p = sniff(filter='port 53', iface=self._iface, timeout=0.3)
        except Exception:
            return False
        else:
            return True

    def sniff_and_analyze(self):
        """
        Performs the sniffing
        """
        # Import things from scapy when I need them in order to reduce memory
        # usage (which is specially big in scapy module, just when importing)
        from scapy.all import sniff

        # Create the filter
        all_ports = self._tcp_ports[:]
        all_ports.extend(self._udp_ports)
        all_ports = list(set(all_ports))
        filter = ' or '.join(['port ' + str(p) for p in all_ports])

        msg = 'ExtrusionServer listening on interface: %s'
        om.out.information(msg % self._iface)

        self._sniffing = True
        try:
            packets = sniff(filter=filter, iface=self._iface, timeout=5)
        except socket.error:
            msg = ('Failed to sniff on interface: "%s". Hints: Are you root?'
                   ' Does this interface exist?')
            msg %= self._iface

            om.out.error(msg)
            raise BaseFrameworkException(msg)

        else:
            self.reverse_ports_allowed = self._analyze_packets(packets)
            return self.reverse_ports_allowed
        finally:
            self._sniffing = False

    def get_result(self):
        while self._sniffing:
            time.sleep(0.5)
        return self.reverse_ports_allowed

    def _analyze_packets_no_host(self, packets):
        """
        Analyze a list of packets for interesting traffic when the host is
        unknown.
        """
        from scapy.all import get_if_addr
        from scapy.all import IP
        from scapy.all import TCP
        from scapy.all import UDP

        # This is hard to do...
        possible_packets = []
        possible_hosts = {}
        good_ports = []
        good_hosts = []

        for p in packets:

            # Analyze TCP
            #
            # 0x2 flag is SYN
            if p.haslayer(TCP) and p[TCP].dport in self._tcp_ports and\
            p[IP].dst in get_if_addr(self._iface) and p[TCP].flags == 0x2:

                possible_packets.append(p)
                if p[IP].src in possible_hosts:
                    possible_hosts[p[IP].src] += 1
                else:
                    possible_hosts[p[IP].src] = 1

            # Analyze UDP
            if p.haslayer(UDP) and p[UDP].dport in self._udp_ports and\
                    p[IP].dst in get_if_addr(self._iface):

                possible_packets.append(p)
                if p[IP].src in possible_hosts:
                    possible_hosts[p[IP].src] += 1
                else:
                    possible_hosts[p[IP].src] = 1

        for p in possible_packets:
            om.out.debug('[extrusionServer] Possible packet: ' + p.summary())

        # Now get the one that has more probability of being the one... and
        # report the list of ports
        def sortfunc(x, y):
            return cmp(x[1], y[1])
        items = possible_hosts.items()
        items.sort(sortfunc)

        # Now I report the ports for the hosts with more connections
        i = 0
        while i < len(items) and items[0][1] == items[i][1]:
            good_hosts.append(items[i][0])
            i += 1

        for p in possible_packets:
            if p[IP].src in good_hosts:
                if p.haslayer(TCP):
                    _tuple = (p[IP].src, p[TCP].dport, 'TCP')
                    if _tuple not in good_ports:
                        good_ports.append(_tuple)
                        om.out.debug('[extrusionServer] Adding ' + str(_tuple))

                if p.haslayer(UDP):
                    _tuple = (p[IP].src, p[UDP].dport, 'UDP')
                    if _tuple not in good_ports:
                        good_ports.append(_tuple)
                        om.out.debug('[extrusionServer] Adding ' + str(_tuple))

        return good_ports

    def _analyze_packets_with_host(self, packets):
        """
        When the host is known it is easier to identify which packets arrived
        from it and which ports are the ones that can be used for reverse shell
        connections.
        """
        from scapy.all import IP
        from scapy.all import TCP
        from scapy.all import UDP

        good_ports = []

        for p in packets:
            if p[TCP] is not None and p[TCP].dport in self._tcp_ports and\
            p[IP].src == self._host and p[TCP].flags == 0x2:

                if (p[IP].src, p[TCP].dport, 'TCP') not in good_ports:
                    good_ports.append((p[IP].src, p[TCP].dport, 'TCP'))

            if p[UDP] is not None and p[UDP].dport in self._udp_ports and\
            p[IP].src == self._host:

                if (p[IP].src, p[UDP].dport, 'UDP') not in good_ports:
                    good_ports.append((p[IP].src, p[UDP].dport, 'UDP'))

        return good_ports

    def _analyze_packets(self, packets):
        """
        Analyze the packets and return a list of ports that can be used by the
        remote host to connect back to the extrusionServer.
        """
        if not packets:
            om.out.debug('No packets captured by scapy.')
            return []
        else:
            msg = 'Analyzing packets captured by scapy. The packets are:'
            om.out.debug(msg)
            for pkt in packets:
                om.out.debug(str(pkt.summary()))

            if self._host is None:
                return self._analyze_packets_no_host(packets)
            else:
                return self._analyze_packets_with_host(packets)
