'''
is_private_site.py

Copyright 2008 Andres Riancho

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
import re

def is_private_site( self, domain_or_IP_address ):
    '''
    @parameter domain_or_IP_address: The domain or IP address that we want to check
    @return: Get the IP address of the domain, return True if its a private address.
    '''
    if re.match('(10\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', domain_or_IP_address) or\
    re.match('(172\.[1-3]\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', domain_or_IP_address) or\
    re.match('(192\.168\.\d?\d?\d?\.\d?\d?\d?)', domain_or_IP_address) or\
    re.match('(127\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', domain_or_IP_address):
        return True
    else:
        addrinfo = None
        try:
            addrinfo = socket.getaddrinfo(domain_or_IP_address, 0)
        except:
            raise w3afException('Could not resolve hostname: ' + domain_or_IP_address )
        else:
            ip_address_list = [info[4][0] for info in addrinfo]
            for ip_address in ip_address_list:
                if re.match('(10\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip_address) or\
                re.match('(172\.[1-3]\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip_address) or\
                re.match('(192\.168\.\d?\d?\d?\.\d?\d?\d?)', ip_address) or\
                re.match('(127\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip_address):
                    return True
    return False
