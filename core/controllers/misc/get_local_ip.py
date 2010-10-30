'''
get_local_ip.py

Copyright 2009 Andres Riancho

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


def get_local_ip():
    '''
    Get the "public" IP address without sending any packets.
    @return: The ip address.
    '''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #   UDP is connection-less, no packets are sent to 4.4.4.2
        #   I use port 80, but could use any port
        sock.connect(('4.4.4.2',80))
        local_address = sock.getsockname()[0]
    except Exception:
        return None
    else:
        return local_address
