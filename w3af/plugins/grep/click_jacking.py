"""
click_jacking.py

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
import w3af.core.data.constants.severity as severity

from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.csp.utils import retrieve_csp_policies


class click_jacking(GrepPlugin):
    """
    Grep every page for missing click jacking protection headers.

    :author: Taras (oxdef@oxdef.info)
    :author: Andres (andres@andresriancho.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        self._total_http_request_count = 0
        self._vuln_count = 0
        self._vuln_urls = DiskSet(table_prefix='click_jacking')
        self._vuln_ids = DiskSet(table_prefix='click_jacking')

    def grep(self, request, response):
        """
        Check x-frame-options header
        """
        if not response.is_text_or_html():
            return

        if is_404(response):
            return

        self._total_http_request_count += 1

        if self._is_protected_against_clickjacking(request, response):
            return

        self._vuln_count += 1
        self._vuln_urls.add(response.get_url())
        self._vuln_ids.add(response.id)

    def _is_protected_against_clickjacking(self, request, response):
        """
        There are many methods to protect a site against clickjacking, this
        method checks for all of them.

        :param request: HTTP request
        :param response: HTTP response
        :return: True if the response is protected
        """
        methods = [
            self._is_protected_with_x_frame_options,
            self._is_protected_with_csp
        ]

        for method in methods:
            if method(request, response):
                return True

        return False

    def _is_protected_with_x_frame_options(self, request, response):
        """
        Check if the HTTP response has the x-frame-options header set
        to the secure value.

        :param request: HTTP request
        :param response: HTTP response
        :return: True if the response is protected
        """
        headers = response.get_headers()
        x_frame_options, header_name = headers.iget('x-frame-options', '')

        if x_frame_options.lower() in ('deny', 'sameorigin'):
            return True

        return False

    def _is_protected_with_csp(self, request, response):
        """
        Check if the HTTP response has a CSP header, parse it, extract the
        frame-ancestors attribute and check it is secure.

        :param request: HTTP request
        :param response: HTTP response
        :return: True if the response is protected
        """
        # These are the policies that will be enforced by the browser
        non_report_only_policies = retrieve_csp_policies(response, False, True)
        frame_ancestors = non_report_only_policies.get('frame-ancestors', [])

        #
        # This is the strictest policy, nobody can frame me!
        #
        # Content-Security-Policy: frame-ancestors 'none';
        #
        for policy in frame_ancestors:
            if policy.lower() == 'none':
                return True

        #
        # Fail when the frame-ancestors has insecure wildcards
        #
        #   Content-Security-Policy: frame-ancestors '*';
        #   Content-Security-Policy: frame-ancestors 'https://*';
        #
        for policy in frame_ancestors:
            if policy.lower() in ('*', 'http', 'https', 'http://', 'https://', 'http://*', 'https://*'):
                return False

        # Content-Security-Policy: frame-ancestors 'self';
        if 'self' in frame_ancestors:
            return True

        # Content-Security-Policy: frame-ancestors 'foo.com' '*.somesite.com';
        if len(frame_ancestors):
            return True

        return False

    def end(self):
        # If all URLs implement protection, don't report anything.
        if not self._vuln_count:
            return

        response_ids = [_id for _id in self._vuln_ids]
        
        # If none of the URLs implement protection, simply report
        # ONE vulnerability that says that
        if self._total_http_request_count == self._vuln_count:
            desc = 'The application has no protection against Click-Jacking attacks'

        # If most of the URLs implement the protection but some
        # don't, report ONE vulnerability saying: "Most are protected,
        # but x, y are not
        else:

            desc = ('Some application URLs have no protection against'
                    ' Click-Jacking attacks. The list of vulnerable URLs is:'
                    '\n\n - ')

            desc += ' - '.join([str(url) + '\n' for url in self._vuln_urls])

        v = Vuln('Click-Jacking vulnerability',
                 desc,
                 severity.MEDIUM,
                 response_ids,
                 self.get_name())
        
        self.kb_append(self, 'click_jacking', v)
        
        self._vuln_urls.cleanup()
        self._vuln_ids.cleanup()

    def get_long_desc(self):
        return """
        This plugin greps every page for X-Frame-Options header and so
        for possible ClickJacking attack against URL.

        Additional information: https://www.owasp.org/index.php/Clickjacking
        """
