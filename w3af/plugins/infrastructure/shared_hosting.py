"""
shared_hosting.py

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
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.search_engines.bing import bing as bing
from w3af.core.data.kb.vuln import Vuln


class shared_hosting(InfrastructurePlugin):
    """
    Use Bing search to determine if the website is in a shared hosting.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # User variables
        self._result_limit = 300

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        domain = fuzzable_request.get_url().get_domain()
        is_public = self._is_public(domain)
        
        if is_public:
            
            ip_address_list = self._get_ip_addresses(domain)
            self._analyze_ips(ip_address_list, fuzzable_request)
    
    def _is_public(self, domain):
        
        if is_private_site(domain):
            msg = 'shared_hosting plugin is not checking for subdomains for'\
                  ' domain: "%s" because it is a private address.' % domain
            om.out.debug(msg)
            return False
        
        return True

    def _get_ip_addresses(self, domain):
        """
        :return: All IP addresses for this domain.
        """
        try:
            addrinfo = socket.getaddrinfo(domain, 0)
        except:
            om.out.error('Failed to resolve address: "%s"' % domain)
            return []

        ip_address_list = [info[4][0] for info in addrinfo]
        ip_address_list = list(set(ip_address_list))
        return ip_address_list
    
    
    def _analyze_ips(self, ip_address_list, fuzzable_request):
        """
        Search all IP addresses in Bing and determine if they have more than
        one domain hosted on it. Store findings in KB.
        """
        bing_wrapper = bing(self._uri_opener)
        
        # This is the best way to search, one by one!
        for ip_address in ip_address_list:
            results = bing_wrapper.get_n_results('ip:' + ip_address,
                                               self._result_limit)

            results = [r.URL.base_url() for r in results]
            results = list(set(results))

            # not vuln by default
            is_vulnerable = False

            if len(results) > 1:
                # We may have something...
                is_vulnerable = True

                if len(results) == 2:
                    # Maybe we have this case:
                    # [Mon 09 Jun 2008 01:08:26 PM ART] - http://216.244.147.14/
                    # [Mon 09 Jun 2008 01:08:26 PM ART] - http://www.business.com/
                    # Where www.business.com resolves to 216.244.147.14; so we don't really
                    # have more than one domain in the same server.
                    try:
                        res0 = socket.gethostbyname(results[0].get_domain())
                        res1 = socket.gethostbyname(results[1].get_domain())
                    except:
                        pass
                    else:
                        if res0 == res1:
                            is_vulnerable = False

            if is_vulnerable:
                desc = 'The web application under test seems to be in a shared' \
                       ' hosting. This list of domains, and the domain of the ' \
                       ' web application under test, all point to the same IP' \
                       ' address (%s):\n' % ip_address
                
                domain_list = kb.kb.raw_read(self, 'domains')
                
                for url in results:
                    domain = url.get_domain()
                    desc += '- %s\n' % domain
                    
                    domain_list.append(domain)
                    
                kb.kb.raw_write(self, 'domains', domain_list)
                    
                v = Vuln.from_fr('Shared hosting', desc, severity.MEDIUM, 1,
                                 self.get_name(), fuzzable_request)

                v['also_in_hosting'] = results
                
                om.out.vulnerability(desc, severity=severity.MEDIUM)
                kb.kb.append(self, 'shared_hosting', v)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        d = 'Fetch the first "result_limit" results from the bing search'
        o = opt_factory('result_limit', self._result_limit, d, 'integer')
        ol.add(o)
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._result_limit = options_list['result_limit'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to find out if the web application under test is stored
        in a shared hosting. The procedure is pretty simple, using bing search
        engine, the plugin searches for "ip:1.2.3.4" where 1.2.3.4 is the IP
        address of the webserver.

        One configurable option exists:
            - result_limit

        Fetch the first "result_limit" results from the "ip:" bing search.
        """
