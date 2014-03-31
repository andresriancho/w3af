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
import socket

from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.misc.levenshtein import relative_distance_lt
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.threads.threadpool import return_args, one_to_many

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

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._first_exec = True
        self._already_queried = ScalableBloomFilter()
        self._can_resolve_domain_names = False

    def discover(self, fuzzable_request):
        """
        Find virtual hosts.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        analysis_result = self._analyze(fuzzable_request)
        self._report_results(fuzzable_request, analysis_result)

    def _analyze(self, fuzzable_request):
        vhost_list = []
        if self._first_exec:
            self._first_exec = False
            vhost_list.extend(self._generic_vhosts(fuzzable_request))

        # I also test for ""dead links"" that the web programmer left in the page
        # For example, If w3af finds a link to "http://corporative.intranet.corp/"
        # it will try to resolve the dns name, if it fails, it will try to request
        # that page from the server
        vhost_list.extend(self._get_dead_links(fuzzable_request))
        return vhost_list

    def _report_results(self, fuzzable_request, analysis_result):
        """
        Report our findings
        """
        reported = set()
        for vhost, request_id in analysis_result:
            if vhost not in reported:
                reported.add(vhost)

                domain = fuzzable_request.get_url().get_domain()
                desc = 'Found a new virtual host at the target web server, the ' \
                       'virtual host name is: "%s". To access this site' \
                       ' you might need to change your DNS resolution settings in' \
                       ' order to point "%s" to the IP address of "%s".'
                desc = desc % (vhost, vhost, domain)
                
                v = Vuln.from_fr('Virtual host identified', desc, severity.LOW,
                                 request_id, self.get_name(), fuzzable_request)
                
                kb.kb.append(self, 'find_vhosts', v)
                om.out.information(v.get_desc())

    def _get_dead_links(self, fuzzable_request):
        """
        Find every link on a HTML document verify if the domain is reachable or
        not; after that, verify if the web found a different name for the target
        site or if we found a new site that is linked. If the link points to a
        dead site then report it (it could be pointing to some private address
        or something...)
        """
        # Get some responses to compare later
        base_url = fuzzable_request.get_url().base_url()
        original_response = self._uri_opener.GET(
            fuzzable_request.get_uri(), cache=True)
        base_response = self._uri_opener.GET(base_url, cache=True)
        base_resp_body = base_response.get_body()

        try:
            dp = parser_cache.dpc.get_document_parser_for(original_response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return []

        # Set the non existant response
        non_existant_response = self._get_non_exist(fuzzable_request)
        nonexist_resp_body = non_existant_response.get_body()

        # Note:
        # - With parsed_references I'm 100% that it's really something in the HTML
        # that the developer intended to add.
        #
        # - The re_references are the result of regular expressions, which in some cases
        # are just false positives.
        #
        # In this case, and because I'm only going to use the domain name of the URL
        # I'm going to trust the re_references also.
        parsed_references, re_references = dp.get_references()
        parsed_references.extend(re_references)

        res = []

        vhosts = self._verify_link_domain(parsed_references)

        for domain, vhost_response in self._send_in_threads(base_url, vhosts):

            vhost_resp_body = vhost_response.get_body()

            if relative_distance_lt(vhost_resp_body, base_resp_body, 0.35) and \
                    relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                res.append((domain, vhost_response.id))
            else:
                desc = 'The content of "%s" references a non existant domain:'\
                       ' "%s". This can be a broken link, or an internal domain'\
                       ' name.'
                desc = desc % (fuzzable_request.get_url(), domain)
                
                i = Info('Internal hostname in HTML link', desc, original_response.id,
                         self.get_name())
                i.set_url(fuzzable_request.get_url())
                
                kb.kb.append(self, 'find_vhosts', i)
                om.out.information(i.get_desc())

        return res

    def _verify_link_domain(self, parsed_references):
        """
        Verify each link in parsed_references and yield the ones that can NOT
        be resolved using DNS.
        """
        for link in parsed_references:
            domain = link.get_domain()

            if domain not in self._already_queried:
                self._already_queried.add(domain)

                try:
                    # raises exception when it's not found
                    # socket.gaierror: (-5, 'No address associated with hostname')
                    socket.gethostbyname(domain)
                except:
                    yield domain

    def _generic_vhosts(self, fuzzable_request):
        """
        Test some generic virtual hosts, only do this once.
        """
        # Get some responses to compare later
        base_url = fuzzable_request.get_url().base_url()
        original_response = self._uri_opener.GET(base_url, cache=True)
        orig_resp_body = original_response.get_body()

        non_existant_response = self._get_non_exist(fuzzable_request)
        nonexist_resp_body = non_existant_response.get_body()

        res = []
        vhosts = self._get_common_virtualhosts(base_url)

        for vhost, vhost_response in self._send_in_threads(base_url, vhosts):
            vhost_resp_body = vhost_response.get_body()

            # If they are *really* different (not just different by some chars)
            if relative_distance_lt(vhost_resp_body, orig_resp_body, 0.35) and \
                    relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                res.append((vhost, vhost_response.id))

        return res

    def _send_in_threads(self, base_url, vhosts):
        base_url_repeater = repeat(base_url)
        args_iterator = izip(base_url_repeater, vhosts)
        http_get = return_args(one_to_many(self._http_get_vhost))
        pool_results = self.worker_pool.imap_unordered(http_get,
                                                          args_iterator)

        for ((base_url, vhost),), vhost_response in pool_results:
            yield vhost, vhost_response

    def _http_get_vhost(self, base_url, vhost):
        """
        Performs an HTTP GET to a URL using a specific vhost.
        :return: HTTPResponse object.
        """
        headers = Headers([('Host', vhost)])
        return self._uri_opener.GET(base_url, cache=False,
                                    headers=headers)

    def _get_non_exist(self, fuzzable_request):
        base_url = fuzzable_request.get_url().base_url()
        non_existant_domain = 'iDoNotExistPleaseGoAwayNowOrDie' + rand_alnum(4)
        return self._http_get_vhost(base_url, non_existant_domain)

    def _get_common_virtualhosts(self, base_url):
        """

        :param base_url: The target URL object.

        :return: A list of possible domain names that could be hosted in the same web
        server that "domain".

        """
        domain = base_url.get_domain()
        root_domain = base_url.get_root_domain()

        common_virtual_hosts = ['intranet', 'intra', 'extranet', 'extra',
                                'test', 'test1', 'old', 'new', 'admin',
                                'adm', 'webmail', 'services', 'console',
                                'apps', 'mail', 'corporate', 'ws', 'webservice',
                                'private', 'secure', 'safe', 'hidden', 'public']

        for subdomain in common_virtual_hosts:
            # intranet
            yield subdomain
            # intranet.www.targetsite.com
            yield subdomain + '.' + domain
            # intranet.targetsite.com
            yield subdomain + '.' + root_domain
            # intranet.targetsite
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
