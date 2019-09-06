"""
detect_reverse_proxy.py

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

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.kb.info import Info


class detect_reverse_proxy(InfrastructurePlugin):
    """
    Find out if the remote web server has a reverse proxy.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        self._proxy_header_list = ['Via', 'Reverse-Via', 'X-Forwarded-For',
                                   'Proxy-Connection', 'Max-Forwards',
                                   'X-Forwarded-Host', 'X-Forwarded-Server']

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        # detect using GET
        if not kb.kb.get('detect_transparent_proxy', 'detect_transparent_proxy'):
            response = self._uri_opener.GET(
                fuzzable_request.get_url(), cache=True)
            if self._has_proxy_headers(response):
                self._report_finding(response)

        # detect using TRACE
        # only if I wasn't able to do it with GET
        if not kb.kb.get('detect_reverse_proxy', 'detect_reverse_proxy'):
            response = self._uri_opener.TRACE(
                fuzzable_request.get_url(), cache=True)
            if self._has_proxy_content(response):
                self._report_finding(response)

        # detect using TRACK
        # This is a rather special case that works with ISA server; example follows:
        # Request:
        # TRACK http://www.xyz.com.bo/ HTTP/1.1
        # ...
        # Response headers:
        # HTTP/1.1 200 OK
        # content-length: 99
        # ...
        # Response body:
        # TRACK / HTTP/1.1
        # Reverse-Via: MUTUN ------> find this!
        # ....
        if not kb.kb.get('detect_reverse_proxy', 'detect_reverse_proxy'):
            response = self._uri_opener.TRACK(
                fuzzable_request.get_url(), cache=True)
            if self._has_proxy_content(response):
                self._report_finding(response)

        # Report failure to detect reverse proxy
        if not kb.kb.get('detect_reverse_proxy', 'detect_reverse_proxy'):
            om.out.information('The remote web server doesn\'t seem to have a reverse proxy.')

    def _report_finding(self, response):
        """
        Save the finding to the kb.

        :param response: The response that triggered the detection
        """
        desc = 'The remote web server seems to have a reverse proxy installed.'

        i = Info('Reverse proxy identified', desc, response.id, self.get_name())
        i.set_url(response.get_url())

        kb.kb.append(self, 'detect_reverse_proxy', i)
        om.out.information(i.get_desc())

    def _has_proxy_headers(self, response):
        """
        Performs the analysis
        :return: True if the remote web server has a reverse proxy
        """
        for proxy_header in self._proxy_header_list:
            for response_header in response.get_headers():
                if proxy_header.upper() == response_header.upper():
                    return True
        return False

    def _has_proxy_content(self, response):
        """
        Performs the analysis of the response of the TRACE and TRACK command.

        :param response: The HTTP response object to analyze
        :return: True if the remote web server has a reverse proxy
        """
        response_body = response.get_body().upper()
        #remove duplicated spaces from body
        whitespace = re.compile('\s+')
        response_body = re.sub(whitespace, ' ', response_body)

        for proxy_header in self._proxy_header_list:
            # Create possible header matches
            possible_matches = [proxy_header.upper(
            ) + ':', proxy_header.upper() + ' :']
            for possible_match in possible_matches:
                if possible_match in response_body:
                    return True
        return False

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
        the current one.
        """
        return ['infrastructure.detect_transparent_proxy']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to determine if the remote end has a reverse proxy
        installed.

        The procedure used to detect reverse proxies is to send a request to
        the remote server and analyze the response headers, if a Via header is
        found, chances are that the remote site has a reverse proxy.
        """
