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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.parsers.url import URL
from w3af.core.data.kb.vuln import Vuln


class xssed_dot_com(InfrastructurePlugin):
    """
    Search in xssed.com to find xssed pages.

    :author: Nicolas Crocfer (shatter@shatter-blog.net)
    :author: Raul Siles: set "." in front of the root domain to limit search
    """
    def __init__(self):
        InfrastructurePlugin.__init__(self)

        #
        #   Could change in time,
        #
        self._xssed_url = URL("http://www.xssed.com")
        self._fixed = "<img src='http://data.xssed.org/images/fixed.gif'>&nbsp;FIXED</th>"

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        """
        Search in xssed.com and parse the output.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        target_domain = fuzzable_request.get_url().get_root_domain()

        try:
            check_url = self._xssed_url.url_join(
                "/search?key=." + target_domain)
            response = self._uri_opener.GET(check_url)
        except BaseFrameworkException, e:
            msg = 'An exception was raised while running xssed_dot_com'\
                  ' plugin. Exception: "%s".' % e
            om.out.debug(msg)
        else:
            #
            #   Only parse the xssed result if we have it,
            #
            try:
                self._parse_xssed_result(response)
            except BaseFrameworkException, e:
                self._exec = True
                msg = 'An exception was raised while running xssed_dot_com'\
                      ' plugin. Exception: "%s".' % e
                om.out.debug(msg)

    def _decode_xssed_url(self, url):
        """
        Replace the URL in the good format.

        :return: None
        """
        url = url.replace('<br>', '')
        url = url.replace('</th>', '')
        url = url.replace('URL: ', '')
        url = url.replace('\r', '')
        url = url.replace('&lt;', '<')
        url = url.replace('&gt;', '>')
        url = url.replace('&quot;', '\'')
        url = url.replace('&amp;', '&')
        return urllib2.unquote(url)

    def _parse_xssed_result(self, response):
        """
        Parse the result from the xssed site and create the corresponding info
        objects.

        :return: Fuzzable requests pointing to the XSS (if any)
        """
        html_body = response.get_body()

        if "<b>XSS:</b>" in html_body:
            #
            #   Work!
            #
            regex_many_vulns = re.findall(
                "<a href='(/mirror/\d*/)' target='_blank'>", html_body)
            for mirror_relative_link in regex_many_vulns:

                mirror_url = self._xssed_url.url_join(mirror_relative_link)
                xss_report_response = self._uri_opener.GET(mirror_url)
                matches = re.findall("URL:.+", xss_report_response.get_body())

                dxss = self._decode_xssed_url

                if self._fixed in xss_report_response.get_body():
                    vuln_severity = severity.LOW
                    desc = 'This script contained a XSS vulnerability: "%s".'
                    desc = desc % dxss(dxss(matches[0]))
                else:
                    vuln_severity = severity.HIGH
                    desc = 'According to xssed.com, this script contains a'\
                           ' XSS vulnerability: "%s".'
                    desc = desc % dxss(dxss(matches[0]))
                    
                v = Vuln('Potential XSS vulnerability', desc,
                         vuln_severity, response.id, self.get_name())

                v.set_url(mirror_url)

                kb.kb.append(self, 'xss', v)
                om.out.information(v.get_desc())

                #
                #   Add the fuzzable request, this is useful if I have the
                #   XSS plugin enabled because it will re-test this and
                #   possibly confirm the vulnerability
                #
                fuzzable_request_list = self._create_fuzzable_requests(
                    xss_report_response)
                return fuzzable_request_list
        else:
            #   Nothing to see here...
            om.out.debug('xssed_dot_com did not find any previously reported'
                         ' XSS vulnerabilities.')

    def get_long_desc(self):
        return """
        This plugin searches the xssed.com database and parses the result. The
        information stored in that database is useful to know about previous
        XSS vulnerabilities in the target website.
        """
