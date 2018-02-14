"""
dns_wildcard.py

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
import re
import socket

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException, RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.info import Info


class dns_wildcard(InfrastructurePlugin):
    """
    Find out if www.site.com and site.com return the same page.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    SIMPLE_IP_RE = re.compile('\d?\d?\d\.\d?\d?\d\.\d?\d?\d\.\d?\d?\d')

    def __init__(self):
        InfrastructurePlugin.__init__(self)

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        """
        Get www.site.com and site.com and compare responses.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """

        # Only do all this if this is a domain name!
        if not self.SIMPLE_IP_RE.match(fuzzable_request.get_url().get_domain()):

            base_url = fuzzable_request.get_url().base_url()
            original_response = self._uri_opener.GET(base_url, cache=True)

            domain = fuzzable_request.get_url().get_domain()
            dns_wildcard_url = fuzzable_request.get_url().copy()

            root_domain = base_url.get_root_domain()
            if len(domain) > len(root_domain):
                # Remove the last subdomain and test with that
                domain_without_subdomain = '.'.join(domain.split('.')[1:])
                dns_wildcard_url.set_domain(domain_without_subdomain)
            else:
                try:
                    socket.gethostbyname(domain)
                except socket.gaierror:
                    # The target is not recognized as an IPv4 address or
                    # domain name because it's a IPv6 address containing [ and
                    # ].
                    return
                dns_wildcard_url.set_domain('foobar.' + domain)

            self._test_DNS(original_response, dns_wildcard_url)
            self._test_IP(original_response, domain)

    def _test_IP(self, original_response, domain):
        """
        Check if http://ip(domain)/ == http://domain/
        """
        try:
            ip_address = socket.gethostbyname(domain)
        except:
            return

        url = original_response.get_url()
        ip_url = url.copy()
        ip_url.set_domain(ip_address)

        try:
            modified_response = self._uri_opener.GET(ip_url, cache=True)
        except BaseFrameworkException, w3:
            msg = 'An error occurred while fetching IP address URL in ' \
                  ' dns_wildcard plugin: "%s"' % w3
            om.out.debug(msg)
        else:
            if fuzzy_not_equal(modified_response.get_body(),
                                    original_response.get_body(), 0.35):

                desc = 'The contents of %s and %s differ.' 
                desc = desc % (modified_response.get_uri(),
                               original_response.get_uri())
                
                i = Info('Default virtual host', desc, modified_response.id,
                         self.get_name())
                i.set_url(modified_response.get_url())

                kb.kb.append(self, 'dns_wildcard', i)
                om.out.information(i.get_desc())

    def _test_DNS(self, original_response, dns_wildcard_url):
        """
        Check if http://www.domain.tld/ == http://domain.tld/
        """
        headers = Headers([('Host', dns_wildcard_url.get_domain())])
        try:
            modified_response = self._uri_opener.GET(
                original_response.get_url(),
                cache=True,
                headers=headers)
        except BaseFrameworkException:
            return
        else:
            if fuzzy_not_equal(modified_response.get_body(),
                                    original_response.get_body(), 0.35):
                desc = 'The target site has NO DNS wildcard, and the contents' \
                       ' of "%s" differ from the contents of "%s".'
                desc = desc % (dns_wildcard_url, original_response.get_url())
                
                i = Info('No DNS wildcard', desc, modified_response.id,
                         self.get_name())
                i.set_url(dns_wildcard_url)

                kb.kb.append(self, 'dns_wildcard', i)
                om.out.information(i.get_desc())
            else:
                desc = 'The target site has a DNS wildcard configuration, the'\
                      ' contents of "%s" are equal to the ones of "%s".'
                desc = desc % (dns_wildcard_url, original_response.get_url())
                
                i = Info('DNS wildcard', desc, modified_response.id,
                         self.get_name())
                i.set_url(original_response.get_url())

                kb.kb.append(self, 'dns_wildcard', i)
                om.out.information(i.get_desc())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin compares the contents of www.site.com and site.com and tries
        to verify if the target site has a DNS wildcard configuration or not.
        """
