"""
is_private_site.py

Copyright 2008 Andres Riancho

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
import ipaddress


def is_private_site(domain_or_ip_address):
    """
    :param domain_or_ip_address: The domain or IP address that we want to check
    :return: Get the IP address of the domain, return True if its a private address.
    """
    if matches_private_ip(domain_or_ip_address):
        return True

    try:
        ip_address = socket.gethostbyname(domain_or_ip_address)
    except socket.gaierror, se:
        # raises exception when it's not found
        if se.errno in (socket.EAI_NODATA, socket.EAI_NONAME):
            return True
    else:
        if matches_private_ip(ip_address):
            return True

    return False


def matches_private_ip(ip_address):
    try:
        return ipaddress.ip_address(ip_address).is_private
    except:
        return False
