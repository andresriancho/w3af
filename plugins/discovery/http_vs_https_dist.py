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

try:
    from scapy import traceroute
except:
    try:
        from extlib.scapy.scapy import traceroute
    except IOError, io:
        import platform
        from core.controllers.w3afException import w3afException
        if 'windows' not in platform.platform().lower():
            raise w3afException('Something strange happened while importing ' \
                                'scapy, please solve this issue: %s' % io)
        else:
            # Windows system!
            raise w3afException('scapy isn\'t installed in your windows ' \
                    'system; please install it following this guide ' \
                    'http://trac.secdev.org/scapy/wiki/WindowsInstallationGuide')

from core.controllers.basePlugin.baseDiscoveryPlugin import \
    baseDiscoveryPlugin
from core.controllers.misc.decorators import runonce
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.parsers.urlParser import getDomain
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afRunOnce, w3afException
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb


PERM_ERROR_MSG = "w3af won't be able to run plugin discovery.http_vs_https_dist." \
" It seems that the user running the w3af process has not enough privileges."

class http_vs_https_dist(baseDiscoveryPlugin):
    '''
    @author: Javier Andalia <jandalia =at= gmail.com>
    '''

    def __init__(self):
        self._http_port = 80
        self._https_port = 443

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzableRequest):
        '''
        Discovery task.
        '''
        if not self._has_permission():
            raise w3afException(PERM_ERROR_MSG) 
        
        http_port = self._http_port
        https_port = self._https_port
        
        def set_info(name, desc):
            inf = info.info()
            inf.setPluginName(self.getName())
            inf.setName(name)
            inf.setDesc(desc)
            kb.kb.append(self, 'httpVsHttpsDist', inf)

        domain = getDomain(fuzzableRequest.getURL())

        # First try with httpS
        https_troute = traceroute(domain, dport=https_port)
        https_troute = https_troute[0].get_trace().values()[0]
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
                         '\'%s\' are different:\n%s\n%s') % \
                         (domain, http_port, https_port, trc1, trc2)
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
        d1 = 'Target http port'
        o1 = option('httpPort', self._http_port, d1, option.INT)
        ol.add(o1)
        d2 = 'Target httpS port'
        o2 = option('httpsPort', self._https_port, d2, option.INT)
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
        giving a detailed report of the traversed hosts in the transit to <target:port>.
        
        Explicitly declared ports on the entered target override the ones specified
        in the config fields.
        
        For example, if the user sets 'http://host.tld:8081' as target and the httpPort
        value is 80; then '8081' will be used.
        
        HTTP and HTTPS ports default to 80 and 443.
        '''
    
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run 
        before the current one.
        '''
        return []

