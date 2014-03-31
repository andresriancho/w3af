"""
private_ip.py

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

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.misc.get_local_ip import get_local_ip
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class private_ip(GrepPlugin):
    """
    Find private IP addresses on the response body and headers.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # For more info regarding this regular expression, please see:
        # https://sourceforge.net/mailarchive/forum.php?thread_name=1955593874.20090122023644%40
        #mlists.olympos.org&forum_name=w3af-develop
        regex_str = '(?<!\.)(?<!\d)(?:(?:10|127)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|192\.168|169\.'
        regex_str += '254|172\.0?(?:1[6-9]|2[0-9]|3[01]))(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-'
        regex_str += '9]?)){2}(?!\d)(?!\.)'
        self._private_ip_address = re.compile(regex_str)
        self._regex_list = [self._private_ip_address, ]

        self._already_inspected = ScalableBloomFilter()
        self._ignore_if_match = None

    def grep(self, request, response):
        """
        Plugin entry point. Search for private IPs in the header and the body.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, results are saved to the kb.
        """
        if self._ignore_if_match is None:
            self._generate_ignores(response)

        if (request.get_url(), request.get_data()) in self._already_inspected:
            return

        # Only run this once for each combination of URL and data sent to
        # that URL
        self._already_inspected.add((request.get_url(), request.get_data()))
        
        self._analyze_headers(request, response)
        self._analyze_html(request, response)
        
        
    def _analyze_headers(self, request, response):
        """
        Search for IP addresses in HTTP headers
        """
        # Get the headers string
        headers_string = response.dump_headers()

        #   Match the regular expressions
        for regex in self._regex_list:
            for match in regex.findall(headers_string):

                # If i'm requesting 192.168.2.111 then I don't want to be
                # alerted about it
                if match not in self._ignore_if_match:
                    desc = 'The URL: "%s" returned an HTTP header with a'\
                           ' private IP address: "%s".'
                    desc = desc % (response.get_url(), match)
                    v = Vuln('Private IP disclosure vulnerability', desc,
                             severity.LOW, response.id, self.get_name())

                    v.set_url(response.get_url())

                    v['IP'] = match
                    v.add_to_highlight(match)
                    self.kb_append(self, 'header', v)

    def _analyze_html(self, request, response):
        """
        Search for IP addresses in the HTML
        """
        if not response.is_text_or_html():
            return

        # Performance improvement!
        if not (('10.' in response) or ('172.' in response) or
               ('192.168.' in response) or ('169.254.' in response)):
            return

        for regex in self._regex_list:
            for match in regex.findall(response.get_body()):
                match = match.strip()

                # Some proxy servers will return errors that include headers in the body
                # along with the client IP which we want to ignore
                if re.search("^.*X-Forwarded-For: .*%s" % match, response.get_body(), re.M):
                    continue

                # If i'm requesting 192.168.2.111 then I don't want to be alerted about it
                if match not in self._ignore_if_match and \
                not request.sent(match):
                    desc = 'The URL: "%s" returned an HTML document'\
                           ' with a private IP address: "%s".'
                    desc = desc % (response.get_url(), match)
                    v = Vuln('Private IP disclosure vulnerability', desc,
                             severity.LOW, response.id, self.get_name())

                    v.set_url(response.get_url())

                    v['IP'] = match
                    v.add_to_highlight(match)
                    self.kb_append(self, 'HTML', v)

    def _generate_ignores(self, response):
        """
        Generate the list of strings we want to ignore as private IP addresses
        """
        if self._ignore_if_match is None:
            self._ignore_if_match = set()

            requested_domain = response.get_url().get_domain()
            self._ignore_if_match.add(requested_domain)

            self._ignore_if_match.add(get_local_ip(requested_domain))
            self._ignore_if_match.add(get_local_ip())

            try:
                ip_address = socket.gethostbyname(requested_domain)
            except:
                pass
            else:
                self._ignore_if_match.add(ip_address)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page body and headers for private IP addresses.
        """
