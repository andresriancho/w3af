"""
server_status.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class server_status(InfrastructurePlugin):
    """
    Find new URLs from the Apache server-status cgi.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._shared_hosting_hosts = []

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Get the server-status and parse it.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        server_status_url = base_url.url_join('server-status')
        response = self._uri_opener.GET(server_status_url, cache=True)

        if not is_404(response) and response.get_code() not in range(400, 404):

            if 'apache' in response.get_body().lower():
                msg = 'Apache server-status module is enabled and accessible.'
                msg += ' The URL is: "%s"' % response.get_url()
                om.out.information(msg)

                self._extract_server_version(fuzzable_request, response)
                self._extract_urls(fuzzable_request, response)
                self._report_shared_hosting(fuzzable_request, response)

    def _extract_server_version(self, fuzzable_request, response):
        """
        Get the server version from the HTML:
            <dl><dt>Server Version: Apache/2.2.9 (Unix)</dt>
        """
        for version in re.findall('<dl><dt>Server Version: (.*?)</dt>',
                                  response.get_body()):
            # Save the results in the KB so the user can look at it
            desc = 'The web server has the apache server status module'\
                   ' enabled which discloses the following remote server'\
                   ' version: "%s".'
            desc %= version
            
            i = Info('Apache Server version', desc, response.id, self.get_name())
            i.set_url(response.get_url())

            om.out.information(i.get_desc())
            kb.kb.append(self, 'server', i)

    def _extract_urls(self, fuzzable_request, response):
        """
        Extract information from the server-status page and send FuzzableRequest
        instances to the core.
        """
        self.output_queue.put(FuzzableRequest(response.get_url()))

        # Now really parse the file and create custom made fuzzable requests
        regex = '<td>.*?<td nowrap>(.*?)</td><td nowrap>.*? (.*?) HTTP/1'
        for domain, path in re.findall(regex, response.get_body()):

            if 'unavailable' in domain:
                domain = response.get_url().get_domain()

            # Check if the requested domain and the found one are equal.
            if domain == response.get_url().get_domain():
                proto = response.get_url().get_protocol()
                found_url = proto + '://' + domain + path
                found_url = URL(found_url)

                # They are equal, request the URL and create the fuzzable
                # requests
                tmp_res = self._uri_opener.GET(found_url, cache=True)
                if not is_404(tmp_res):
                    self.output_queue.put(FuzzableRequest(found_url))
            else:
                # This is a shared hosting server
                self._shared_hosting_hosts.append(domain)

    def _report_shared_hosting(self, fuzzable_request, response):
        # Now that we are outsite the for loop, we can report the possible vulns
        if len(self._shared_hosting_hosts):
            desc = 'The web application under test seems to be in a shared'\
                   ' hosting.'
            v = Vuln.from_fr('Shared hosting', desc, severity.MEDIUM,
                             response.id, self.get_name(), fuzzable_request)

            self._shared_hosting_hosts = list(set(self._shared_hosting_hosts))
            v['also_in_hosting'] = self._shared_hosting_hosts

            kb.kb.append(self, 'shared_hosting', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

            msg = 'This list of domains, and the domain of the web application'\
                  ' under test, all point to the same server:'
            om.out.vulnerability(msg, severity=v.get_severity())
            for url in self._shared_hosting_hosts:
                om.out.vulnerability('- ' + url, severity=severity.MEDIUM)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin fetches the server-status file used by Apache, and parses it.
        After parsing, new URLs are found, and in some cases, the plugin can deduce
        the existence of other domains hosted on the same server.
        """
