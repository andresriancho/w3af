'''
http_vs_https_dist.py

Copyright 2011 Andres Riancho

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

from scapy.all import traceroute

from core.controllers.basePlugin.baseDiscoveryPlugin import \
    baseDiscoveryPlugin
from core.controllers.misc.decorators import runonce
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.w3afException import w3afRunOnce, w3afException
import core.controllers.outputManager as om
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as uparser


PERM_ERROR_MSG = "w3af won't be able to run plugin discovery.http_vs_https_dist." \
" It seems that the user running the w3af process has not enough privileges."

class http_vs_https_dist(baseDiscoveryPlugin):
    '''
    Determines the network distance between the http and https ports for a target.
    @author: Javier Andalia <jandalia =at= gmail.com>
    '''

    def __init__(self):
        self._http_port = 80
        self._https_port = 443

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzableRequest):
        '''
        Discovery task. Uses scapy.traceroute function in order to determine
        the distance between http and https ports for the target.
        Intended to be executed once during the discovery process.
        '''
        if not self._has_permission():
            raise w3afException(PERM_ERROR_MSG) 
        
        def set_info(name, desc):
            inf = info.info()
            inf.setPluginName(self.getName())
            inf.setName(name)
            inf.setDesc(desc)
            kb.kb.append(self, 'http_vs_https_dist', inf)

        target_url = fuzzableRequest.getURL()
        domain = uparser.getDomain(target_url)
        http_port = self._http_port
        https_port = self._https_port

        # Use target port if specified
        netloc = uparser.getNetLocation(target_url)
        try:
            port = int(netloc.split(':')[-1])
        except ValueError:
            pass # Nothing to do.
        else:
            protocol = uparser.getProtocol(target_url)
            if protocol == 'https':
                https_port = port
            else: # it has to be 'http'
                http_port = port

        # First try with httpS
        https_troute = traceroute(domain, dport=https_port)[0].get_trace()
        
        # This destination was probably 'localhost' or a host reached through
        # a vpn?
        if not https_troute:
            return []
        
        https_troute = https_troute.values()[0]
        https_ip_tuples = https_troute.values()
        last_https_ip = https_ip_tuples[-1]
        
        # Then with http
        http_troute = traceroute(domain, dport=http_port)
        http_troute = http_troute[0].get_trace().values()[0]
        http_ip_tuples = http_troute.values()
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
            # Are routes different
            if http_ip_tuples != https_ip_tuples:
                header = '  TCP trace to %s:%s\n%s'
                trace_str = lambda iptuples: '\n'.join('    %s %s' % \
                                (t[0], t[1][0]) for t in enumerate(iptuples))

                trc1 = header % (domain, http_port, trace_str(http_ip_tuples))
                trc2 = header % (domain, https_port, trace_str(https_ip_tuples))

                desc = _('Routes to target \'%s\' using ports \'%s\' and ' \
                '\'%s\' are different:\n%s\n%s') % (domain, http_port, 
                                                    https_port, trc1, trc2)
                set_info('HTTP vs. HTTPS Distance', desc)
                om.out.information(desc)
        return []

    def _has_permission(self):
        '''
        Return boolean value that indicates if the user running w3af has
        enough privileges to exec 'traceroute'
        '''
        try:
            traceroute('127.0.0.1', maxttl=1)
        except socket.error:
            return False
        return True

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        d1 = 'Destination http port number to analize'
        o1 = option('httpPort', self._http_port, d1, option.INT, help=d1)
        ol.add(o1)
        
        d2 = 'Destination httpS port number to analize'
        o2 = option('httpsPort', self._https_port, d2, option.INT, help=d2)
        ol.add(o2)
        
        return ol

    def setOptions(self, options):
        '''
        Sets all the options that are configured using the UI generated by
        the framework using the result of getOptions().
        
        @parameter options: A dictionary with the options for the plugin.
        '''
        self._http_port = options['httpPort'].getValue()            
        self._https_port = options['httpsPort'].getValue()
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin analyzes the network distance between the HTTP and HTTPS ports
        giving a detailed report of the traversed hosts in transit to <target:port>.
        You should have root/admin privileges in order to run this plugin succesfully.
        
        Explicitly declared ports on the entered target override those specified
        in the config fields.        
        For example, if the user sets 'https://host.tld:444' as target and the httpPort
        value is 443; then '444' will be used.
        
        HTTP and HTTPS ports default to 80 and 443.
        '''
    
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run 
        before the current one.
        '''
        return []

