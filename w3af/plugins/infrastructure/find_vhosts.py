"""
find_vhosts.py

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
from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.threads.threadpool import return_args, one_to_many
from w3af.core.controllers.misc.is_ip_address import is_ip_address
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class find_vhosts(InfrastructurePlugin):
    """
    Modify the HTTP Host header and try to find virtual hosts.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    COMMON_VHOSTS = ['intranet', 'intra', 'extranet', 'extra', 'test',
                     'test1', 'old', 'new', 'admin', 'adm', 'webmail',
                     'services', 'console', 'apps', 'mail', 'corporate',
                     'ws', 'webservice', 'private', 'secure', 'safe',
                     'hidden', 'public']

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._first_exec = True
        self._already_queried_dns = ScalableBloomFilter()

    def discover(self, fuzzable_request, debugging_id):
        """
        Find virtual hosts.

        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        if self._first_exec:
            self._first_exec = False

            self._check_potential_vhosts(fuzzable_request,
                                         self._get_common_virtual_hosts(fuzzable_request))

        # Also test for ""dead links"" that the web developer left in the
        # page. For example, if w3af finds a link to:
        #
        #   "http://corp.intranet.com/"
        #
        # It will try to resolve the DNS name, if it fails, it will try
        # to request that page from the server
        self._check_potential_vhosts(fuzzable_request,
                                     self._get_dead_domains(fuzzable_request))

    def _get_dead_domains(self, fuzzable_request):
        """
        Find every link on a HTML document verify if the domain can be resolved

        :return: Yield domains that can not be resolved or resolve to a private
                 IP address
        """
        original_response = self._uri_opener.GET(fuzzable_request.get_uri(), cache=True)

        try:
            dp = parser_cache.dpc.get_document_parser_for(original_response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        # Note:
        #
        # - With parsed_references I'm 100% that it's really something in the
        #   HTML that the developer intended to add.
        #
        # - The re_references are the result of regular expressions, which in
        #   some cases are just false positives.
        #
        # In this case, and because I'm only going to use the domain name of the
        # URL I'm going to trust the re_references also.
        parsed_references, re_references = dp.get_references()
        parsed_references.extend(re_references)

        for link in parsed_references:
            domain = link.get_domain()

            if domain in self._already_queried_dns:
                continue

            self._already_queried_dns.add(domain)

            if not is_private_site(domain):
                continue

            desc = (u'The content of "%s" references a non existent domain: "%s".'
                    u' This can be a broken link, or an internal domain name.')
            desc %= (fuzzable_request.get_url(), domain)

            i = Info(u'Internal hostname in HTML link', desc,
                     original_response.id, self.get_name())
            i.set_url(fuzzable_request.get_url())

            kb.kb.append(self, 'find_vhosts', i)
            om.out.information(i.get_desc())

            yield domain

    def _check_potential_vhosts(self, fuzzable_request, vhosts):
        """
        Send the HTTP requests to check for potential findings

        :param fuzzable_request: The fuzzable request as received by the plugin
        :param vhosts: A generator yielding potential vhosts to check
        :return: None, vulnerabilities (if any) are written to the KB
        """
        # Get some responses to compare later
        base_url = fuzzable_request.get_url().base_url()
        original_response = self._uri_opener.GET(base_url, cache=True)
        orig_resp_body = original_response.get_body()

        non_existent_responses = self._get_non_exist(fuzzable_request)

        for vhost, vhost_response in self._send_in_threads(base_url, vhosts):

            if not self._response_is_different(vhost_response, orig_resp_body, non_existent_responses):
                continue

            domain = fuzzable_request.get_url().get_domain()
            desc = (u'Found a new virtual host at the target web server, the'
                    u' virtual host name is: "%s". To access this site'
                    u' you might need to change your DNS resolution settings'
                    u' in order to point "%s" to the IP address of "%s".')
            desc %= (vhost, vhost, domain)

            ids = [vhost_response.id, original_response.id]
            ids.extend([r.id for r in non_existent_responses])

            v = Vuln.from_fr('Virtual host identified', desc, severity.LOW,
                             ids, self.get_name(), fuzzable_request)

            kb.kb.append(self, 'find_vhosts', v)
            om.out.information(v.get_desc())

    def _response_is_different(self, vhost_response, orig_resp_body, non_existent_responses):
        """
        Note that we use 0.35 in fuzzy_equal because we want the responses to be
        *really different*.

        :param vhost_response: The HTTP response body for the virtual host
        :param orig_resp_body: The original HTTP response body
        :param non_existent_responses: One or more HTTP responses for virtual hosts
                                       that do not exist in the remote server
        :return: True if vhost_response is different from orig_resp_body and non_existent_responses
        """
        if fuzzy_equal(vhost_response.get_body(), orig_resp_body, 0.35):
            return False

        for ner in non_existent_responses:
            if fuzzy_equal(vhost_response.get_body(), ner.get_body(), 0.35):
                return False

        return True

    def _send_in_threads(self, base_url, vhosts):
        base_url_repeater = repeat(base_url)
        args_iterator = izip(base_url_repeater, vhosts)
        http_get = return_args(one_to_many(self._http_get_vhost))
        pool_results = self.worker_pool.imap_unordered(http_get, args_iterator)

        for ((base_url, vhost),), vhost_response in pool_results:
            yield vhost, vhost_response

    def _http_get_vhost(self, base_url, vhost):
        """
        Performs an HTTP GET to a URL using a specific vhost.
        :return: HTTPResponse object.
        """
        headers = Headers([('Host', vhost)])
        return self._uri_opener.GET(base_url, cache=False, headers=headers)

    def _get_non_exist(self, fuzzable_request):
        """
        :param fuzzable_request: The original fuzzable request
        :return: One or more HTTP responses which are returned by the application
                 when the Host header contains a domain that does not exist
                 in the remote server
        """
        base_url = fuzzable_request.get_url().base_url()

        # One for the TLD
        non_existent_domain = 'iDoNotExistPleaseGoAwayNowOrDie%s.com' % rand_alnum(4)

        # One for subdomain
        args = (rand_alnum(4), base_url.get_domain())
        non_existent_subdomain = 'iDoNotExistPleaseGoAwayNowOrDie%s.%s' % args

        result = []

        for ne_domain in (non_existent_domain, non_existent_subdomain):
            try:
                http_response = self._http_get_vhost(base_url, ne_domain)
            except Exception, e:
                msg = 'Failed to generate invalid domain fingerprint: %s'
                om.out.debug(msg % e)
            else:
                result.append(http_response)

        return result

    def _get_common_virtual_hosts(self, fuzzable_request):
        """
        Get a list of common virtual hosts based on the target domain

        :param fuzzable_request: The fuzzable request as received by the plugin
        :return: A list of possible domain names that could be hosted in the
                 same web server that "domain".
        """
        base_url = fuzzable_request.get_url().base_url()
        domain = base_url.get_domain()
        root_domain = base_url.get_root_domain()

        for subdomain in self.COMMON_VHOSTS:
            # intranet
            yield subdomain

            # It doesn't make any sense to create subdomains based no an
            # IP address, they will look like intranet.192.168.1.2 , and
            # are invalid domains
            if is_ip_address(domain):
                continue

            # intranet.www.target.com
            yield subdomain + '.' + domain
            # intranet.target.com
            yield subdomain + '.' + root_domain
            # intranet.target
            yield subdomain + '.' + root_domain.split('.')[0]

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin uses the HTTP Host header to find new virtual hosts. For
        example, if the intranet page is hosted in the same server that the
        public page, and the web server is misconfigured, this plugin will
        discover that virtual host.

        Please note that this plugin doesn't use any DNS technique to find
        these virtual hosts.
        """
