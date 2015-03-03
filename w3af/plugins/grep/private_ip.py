"""
private_ip.py

Copyright 2015 Andres Riancho

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
from w3af.core.data.kb.info_set import InfoSet


class private_ip(GrepPlugin):
    """
    Find private IP addresses on the response body and headers.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # More info regarding this regular expression: http://bit.ly/185DFJc
    IP_RE = '(?<!\.)(?<!\d)(?:(?:10|127)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9]' \
            '[0-9]?)|192\.168|169\.254|172\.0?(?:1[6-9]|2[0-9]|3[01]))' \
            '(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){2}(?!\d)(?!\.)'

    RE_LIST = [re.compile(IP_RE)]

    def __init__(self):
        GrepPlugin.__init__(self)

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

    def _get_header_name(self, response, ip_address, regex):
        for header_name, header_value in response.get_headers().iteritems():
            for header_ip_address in regex.findall(header_value):
                header_ip_address = header_ip_address.strip()
                if header_ip_address == ip_address:
                    return header_name

        return None

    def _analyze_headers(self, request, response):
        """
        Search for IP addresses in HTTP headers
        """
        # Get the headers string
        headers_string = response.dump_headers()

        # Match the regular expressions
        for regex in self.RE_LIST:
            for ip_address in regex.findall(headers_string):
                ip_address = ip_address.strip()

                # If i'm requesting 192.168.2.111 then I don't want to be
                # alerted about it
                if ip_address in self._ignore_if_match:
                    continue

                # I want to know the header name, this shouldn't consume much
                # CPU since we're only doing it when the headers already match
                # the initial regex run
                header_name = self._get_header_name(response, ip_address, regex)

                desc = 'The URL "%s" returned the private IP address: "%s"'\
                       ' in the HTTP response header "%s"'
                desc = desc % (response.get_url(), ip_address, header_name)

                v = Vuln('Private IP disclosure vulnerability', desc,
                         severity.LOW, response.id, self.get_name())

                v.set_url(response.get_url())
                v.add_to_highlight(ip_address)
                v['ip_address'] = ip_address
                v['header_name'] = header_name
                v[HeaderPrivateIPInfoSet.ITAG] = (ip_address, header_name)

                self.kb_append_uniq_group(self, 'header', v,
                                          group_klass=HeaderPrivateIPInfoSet)

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

        for regex in self.RE_LIST:
            for ip_address in regex.findall(response.get_body()):
                ip_address = ip_address.strip()

                # Some proxy servers will return errors that include headers
                # in the body along with the client IP which we want to ignore
                if re.search("^.*X-Forwarded-For: .*%s" % ip_address,
                             response.get_body(), re.M):
                    continue

                # If i'm requesting 192.168.2.111 then I don't want to be
                # alerted about it
                if ip_address in self._ignore_if_match:
                    continue

                # Don't match things I've sent
                if request.sent(ip_address):
                    continue

                desc = 'The URL: "%s" returned an HTML document which' \
                       ' contains the private IP address: "%s".'
                desc = desc % (response.get_url(), ip_address)
                v = Vuln('Private IP disclosure vulnerability', desc,
                         severity.LOW, response.id, self.get_name())

                v.set_url(response.get_url())
                v.add_to_highlight(ip_address)
                v[HTMLPrivateIPInfoSet.ITAG] = ip_address

                self.kb_append_uniq_group(self, 'HTML', v,
                                          group_klass=HTMLPrivateIPInfoSet)

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


class HTMLPrivateIPInfoSet(InfoSet):
    ITAG = 'ip_address'
    TEMPLATE = (
        'A total of {{ uris|length }} HTTP responses contained the private IP'
        ' address {{ ip_address }} in the response body. The first ten'
        ' matching URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class HeaderPrivateIPInfoSet(InfoSet):
    ITAG = 'group_by'
    TEMPLATE = (
        'A total of {{ uris|length }} HTTP responses contained the private IP'
        ' address {{ ip_address }} in the "{{ header_name }}" response header.'
        ' The first ten matching URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )