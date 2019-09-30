"""
xssed_dot_com.py

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
import urllib2

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.parsers.utils.encode_decode import htmldecode
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class xssed_dot_com(InfrastructurePlugin):
    """
    Search in xssed.com to find xssed pages.

    :author: Nicolas Crocfer (shatter@shatter-blog.net)
    :author: Raul Siles: set "." in front of the root domain to limit search
    """
    #
    #   Depends on xssed.com, we need to keep these updated
    #
    UNFIXED = 'UNFIXED'
    XSSED_URL = URL('http://www.xssed.com')
    XSSED_URL_RE = re.compile('URL: (.*?)</th>')
    XSSED_DOMAIN_RE = re.compile("<a href='(/mirror/\d*/)' target='_blank'>")

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Search in xssed.com and parse the output.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        target_domain = fuzzable_request.get_url().get_root_domain()
        target_path = '/search?key=.%s' % target_domain
        check_url = self.XSSED_URL.url_join(target_path)

        try:
            response = self._uri_opener.GET(check_url)
        except BaseFrameworkException, e:
            msg = ('An exception was raised while running xssed_dot_com'
                   ' plugin. Exception: "%s".')
            om.out.debug(msg % e)
        else:
            self._parse_xssed_search_result(response)

    def _parse_xssed_search_result(self, response):
        """
        Parse the search result from the xssed site and create the
        corresponding info objects.
        """
        xssed_matches = self.XSSED_DOMAIN_RE.findall(response.get_body())

        for mirror_relative_link in xssed_matches:

            mirror_url = self.XSSED_URL.url_join(mirror_relative_link)

            try:
                xss_report_response = self._uri_opener.GET(mirror_url)
            except BaseFrameworkException, e:
                msg = ('An exception was raised while running xssed_dot_com'
                       ' plugin. Exception: "%s".')
                om.out.debug(msg % e)
                continue
            else:
                self._parse_xssed_vuln_page(xss_report_response)
        else:
            # Nothing to see here...
            om.out.debug('xssed_dot_com did not find any previously reported'
                         ' XSS vulnerabilities.')

    def _parse_xssed_vuln_page(self, xss_report_response):
        """
        Parse the HTTP response for a vulnerability page such as
        http://www.xssed.com/mirror/76754/ and create the vulnerability object
        to the KB.
        """
        body = xss_report_response.get_body()
        url_matches = self.XSSED_URL_RE.findall(body)

        for xss_url in url_matches:

            # Ugly but required because of how xssed.com writes stuff
            xss_url = xss_url.replace('<br>', '')
            xss_url = htmldecode(xss_url)
            xss_url = urllib2.unquote(xss_url)
            xss_url = URL(xss_url)

            if self.UNFIXED in xss_report_response.get_body():
                vuln_severity = severity.HIGH
                verb = 'contains'
            else:
                vuln_severity = severity.LOW
                verb = 'contained'

            desc_fmt = ('According to xssed.com the target domain %s a XSS'
                        ' vulnerability, see %s for more information')
            desc = desc_fmt % (verb, xss_report_response.get_url())
            v = Vuln('Potential XSS vulnerability', desc,
                     vuln_severity, xss_report_response.id, self.get_name())
            v.set_url(xss_url)

            #
            # Add the fuzzable request, this is useful if I have the
            # XSS plugin enabled because it will re-test this and
            # possibly confirm the vulnerability
            #
            fr = FuzzableRequest(xss_url)
            self.output_queue.put(fr)

            # Save the vuln to the KB and print to output
            self.kb_append(self, 'xss', v)

    def get_long_desc(self):
        return """
        This plugin searches the xssed.com database and parses the result. The
        information stored in that database is useful to know about previous
        XSS vulnerabilities in the target website.
        """
