"""
http_vs_https_dist.py

Copyright 2011 Andres Riancho

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
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INT
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.data.kb.info import Info


PERM_ERROR_MSG = ("w3af won't be able to run plugin infrastructure.http_vs_"
                  "https_dist. It seems that the user running the w3af process"
                  " has not enough privileges.")


class http_vs_https_dist(InfrastructurePlugin):
    """
    Determines the network distance between the http and https ports for a target

    :author: Javier Andalia <jandalia =at= gmail.com>
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        self._http_port = 80
        self._https_port = 443

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Discovery task. Uses scapy.traceroute function in order to determine
        the distance between http and https ports for the target.
        Intended to be executed once during the infrastructure process.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if not self._has_permission():
            om.out.error(PERM_ERROR_MSG)
            return

        def set_info(name, desc):
            i = Info(name, desc, 1, self.get_name())
            kb.kb.append(self, 'http_vs_https_dist', i)

        target_url = fuzzable_request.get_url()
        domain = target_url.get_domain()
        http_port = self._http_port
        https_port = self._https_port

        # Use target port if specified
        netloc = target_url.get_net_location()
        try:
            port = int(netloc.split(':')[-1])
        except ValueError:
            pass  # Nothing to do.
        else:
            protocol = target_url.get_protocol()
            if protocol == 'https':
                https_port = port
            else:  # it has to be 'http'
                http_port = port

        # Import things from scapy when I need them in order to reduce memory
        # usage (which is specially big in scapy module, just when importing)
        try:
            from scapy.all import traceroute
        except ImportError, ie:
            om.out.debug('There was an error importing scapy.all: "%s"' % ie)
            return

        try:
            # pylint: disable=E1124,E1136

            # First try with httpS
            https_troute = traceroute(domain, dport=https_port)[0].get_trace()
            # Then with http
            http_troute = traceroute(domain, dport=http_port)[0].get_trace()

            # pylint: enable=E1124,E1136
        except Exception, e:
            # I've seen numerous bug reports with the following exception:
            # "error: illegal IP address string passed to inet_aton"
            # that come from this part of the code. It seems that in some cases
            # the domain resolves to an IPv6 address and scapy does NOT
            # support that protocol.
            om.out.debug('There was an error running scapy\'s traceroute: "%s"' % e)
            return

        # This destination was probably 'localhost' or a host reached
        # through a vpn?
        if not (https_troute and http_troute):
            return

        https_ip_tuples = https_troute.values()[0].values()
        last_https_ip = https_ip_tuples[-1]
        http_ip_tuples = http_troute.values()[0].values()
        last_http_ip = http_ip_tuples[-1]

        # Last IP should be True; otherwise the dest wasn't reached
        # Tuples have the next form: ('192.168.1.1', False)
        if not (last_https_ip[1] and last_http_ip[1]):
            desc = _('The port \'%s\' is not open on target %s')
            if not last_https_ip[1]:
                om.out.error(desc % (https_port, domain))
            if not last_http_ip[1]:
                om.out.error(desc % (http_port, domain))
        else:
            trace_str = lambda iptuples: '\n'.join('    %s %s' %
                                                  (t[0], t[1][0]) for t in enumerate(iptuples))

            if http_ip_tuples != https_ip_tuples:
                header = '  TCP trace to %s:%s\n%s'

                trc1 = header % (domain, http_port, trace_str(http_ip_tuples))
                trc2 = header % (
                    domain, https_port, trace_str(https_ip_tuples))

                desc = 'Routes to target "%s" using ports %s and ' \
                       '%s are different:\n%s\n%s'
                desc %= (domain, http_port, https_port, trc1, trc2)
                set_info('HTTP and HTTPs hop distance', desc)
                om.out.information(desc)
            else:
                desc = 'The routes to the target\'s HTTP and HTTPS ports are' \
                       ' the same:\n%s' % trace_str(http_ip_tuples)
                set_info('HTTP traceroute', desc)

    # pylint: disable=E0202
    # An attribute affected in plugins.tests.infrastructure.
    # test_http_vs_https_dist line 53 hide this method
    def _has_permission(self):
        """
        Return boolean value that indicates if the user running w3af has
        enough privileges to exec 'traceroute'
        """
        # Import things from scapy when I need them in order to reduce memory
        # usage (which is specially big in scapy module, just when importing)
        try:
            from scapy.all import traceroute
            from scapy.error import Scapy_Exception
        except socket.error:
            # [Errno 1] Operation not permitted #12131
            # https://github.com/andresriancho/w3af/issues/12131
            return False

        try:
            traceroute('127.0.0.1', maxttl=1)
        except socket.error:
            return False
        except Scapy_Exception:
            return False
        except:
            return False
            
        return True
    # pylint: enable=E0202

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        d1 = 'Destination http port number to analize'
        o1 = opt_factory('httpPort', self._http_port, d1, INT, help=d1)
        ol.add(o1)

        d2 = 'Destination httpS port number to analize'
        o2 = opt_factory('httpsPort', self._https_port, d2, INT, help=d2)
        ol.add(o2)

        return ol

    def set_options(self, options):
        """
        Sets all the options that are configured using the UI generated by
        the framework using the result of get_options().

        :param options: A dictionary with the options for the plugin.
        """
        self._http_port = options['httpPort'].get_value()
        self._https_port = options['httpsPort'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin analyzes the network distance between the HTTP and HTTPS ports
        giving a detailed report of the traversed hosts in transit to <target:port>.
        You should have root/admin privileges in order to run this plugin succesfully.

        Explicitly declared ports on the entered target override those specified
        in the config fields.
        For example, if the user sets 'https://host.tld:444' as target and the httpPort
        value is 443; then '444' will be used.

        HTTP and HTTPS ports default to 80 and 443.
        """
