"""
detect_transparent_proxy.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.kb.info import Info


class detect_transparent_proxy(InfrastructurePlugin):
    """
    Find out if your ISP has a transparent proxy installed.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if self._is_proxyed_conn(fuzzable_request):
            desc = 'Your ISP seems to have a transparent proxy installed,'\
                   ' this can influence scan results in unexpected ways.'
           
            i = Info('Transparent proxy detected', desc, 1, self.get_name())
            i.set_url(fuzzable_request.get_url())
            
            kb.kb.append(self, 'detect_transparent_proxy', i)
            om.out.information(i.get_desc())
        else:
            om.out.information('Your ISP has no transparent proxy.')

    def _is_proxyed_conn(self, fuzzable_request):
        """
        Make a connection to a "random" IP to port 80 and make a request for the
        URL we are interested in.

        :return: True if proxy is present.
        """
        random_ips = ['1.2.3.4', '5.6.7.8', '9.8.7.6', '1.2.1.2', '1.0.0.1',
                      '60.60.60.60', '44.44.44.44', '11.22.33.44', '11.22.33.11',
                      '7.99.7.99', '87.78.87.78']

        for ip_address in random_ips:
            sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock_obj.connect((ip_address, 80))
            except:
                return False
            else:
                continue

        return True

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to detect transparent proxies.

        The procedure for detecting transparent proxies is simple, I try to connect
        to a series of IP addresses, to the port 80, if all of them return an opened
        socket, then it's the proxy server responding.
        """
