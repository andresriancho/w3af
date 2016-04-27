"""
csp.py

Copyright 2013 Andres Riancho

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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.csp.utils import CSP
from w3af.core.data.kb.vuln import Vuln

class csp(GrepPlugin):
    """
    Identifies incorrect or too permissive Content Security Policy headers.
    """
    VULN_NAME = 'CSP vulnerability'
    _trusted_hosts = []
    _source_limit = 10
    _report_eval = True
    _report_no_report_uri = False
    
    def __init__(self):
        """
        Class init
        """
        GrepPlugin.__init__(self)
        self._responses_without_csp = set()
        # We don't use disk_* here because 
        # the list should be too small for such storage
        # e.g. it is common for web app to have only **one** CSP policy
        self.csps = set()
        self.csp_cache = []
                
    def grep(self, request, response):
        """
        Perform search on current HTTP request/response exchange.
        Store information about vulns for further global processing.
        
        :param request: HTTP request
        :param response: HTTP response  
        """
        without_csp_limit = 10
        csp_cache_limit = 3
        csp = CSP()
        csp.source_limit = self._source_limit
        csp.trusted_hosts = self._trusted_hosts
        csp.report_eval = self._report_eval
        csp.report_no_report_uri = self._report_no_report_uri
        if csp.init_from_response(response): 
            self.csps.add(csp)
            if len(self.csp_cache) < csp_cache_limit:
                self.csp_cache.append(csp)
        elif len(self._responses_without_csp) < without_csp_limit:
            self._responses_without_csp.add((response.id, 
                response.get_url().uri2url()))

    def end(self):
        """
        Perform global analysis for all vulnerabilities found.
        """
        csp_vulns = ""
        result = ""

        # The whole target has no CSP protection
        if not self.csps:
            result = self.vuln_tpl % self.vuln_no_csp_tpl
            v = Vuln(self.VULN_NAME, result, severity.MEDIUM, 
                    [r[0] for r in self._responses_without_csp],
                    self.get_name())
            self.kb_append(self, 'csp', v)
            return

        # Vulns in csps
        for csp in self.csps:
            tmp = ""
            for policy in csp.policies:
                if policy.find_vulns():
                    vulns = " * " + "\n * ".join([v.desc for v in policy.find_vulns()])
                    tmp += self.policy_tpl % (policy.pretty(), vulns)
            if tmp:
                csp_vulns += "URL: %s" % csp.response_url + tmp
        
        if csp_vulns:
            result += self.vuln_csp_tpl + csp_vulns

        # If there were found URLs without CSP
        if self._responses_without_csp:
            csp_vulns_detected = True
            result += self.vuln_without_tpl % "\n".join(
                    [r[1] for r in self._responses_without_csp])
        
        # Try to find weak nonces
        if len(self.csp_cache) > 1:
            csp = self.csp_cache[0]
            nonce_vulns = csp.find_nonce_vulns(self.csp_cache[1:])
            if nonce_vulns:
                vulns = " * " + "\n * ".join([v.desc for v in nonce_vulns])
                result += self.common_tpl % vulns

        if result:
            v = Vuln(self.VULN_NAME, self.vuln_tpl % result, severity.MEDIUM, 
                    [csp.response_id for csp in self.csps],
                    self.get_name())
            self.kb_append(self, 'csp', v)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Maximum number limit of sources in source list of directive'
        h = ('The plugin will report a vulnerability when detects '
        'that number of sources in source list of any directive '
        'is bigger then this limit.')
        o = opt_factory('source_limit', self._source_limit, d, 'integer', help=h)
        ol.add(o)

        d = 'List of trusted hosts for finding untrusted ones in source list of directive'
        h = ('The plugin will report a vulnerability when detects '
        'that source list of any directive contains untrusted host')
        o = opt_factory('trusted_hosts', self._trusted_hosts, d, 'list', help=h)
        ol.add(o)

        d = "Report when detects usage of 'unsafe-eval' in source list of directive"
        h = ("Unfortunately it is very hard to switch off 'unsafe-eval' "
        'in e.g. script-src directive because a lot of JS staff use eval().')
        o = opt_factory('report_eval', self._report_eval, d, 'boolean', help=h)
        ol.add(o)

        d = 'Report when detects that report-uri directive is not set'
        h = ('Monitoring a policy is useful for testing whether '
                'enforcing the policy will cause the web application to malfunction. '
                'The plugin will report when detects that report-uri directive is not set')
        o = opt_factory('report_no_report_uri', self._report_no_report_uri, d, 'boolean', help=h)
        ol.add(o)

        return ol

    def set_options(self, option_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().
        
        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """

        self._source_limit = option_list['source_limit'].get_value()
        self._trusted_hosts = option_list['trusted_hosts'].get_value()
        self._report_eval = option_list['report_eval'].get_value()
        self._report_no_report_uri = option_list['report_no_report_uri'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies incorrect or too permissive Content Security Policy version 2 
        (CSP) policy returned by the web application under analysis.

        Additional information:

         * https://www.owasp.org/index.php/Content_Security_Policy
         * http://www.w3.org/TR/CSP

        There are some configurable parameters:
            - source_limit
            - trusted_hosts
        """        

    vuln_csp_tpl = """
There were identified incorrect or too permissive CSP2
policies returned by the web application under analysis.

"""

    vuln_tpl = """
Content Security Policy related information

%s

Additional information: 

 * https://www.owasp.org/index.php/Content_Security_Policy
 * http://www.w3.org/TR/CSP

"""

    policy_tpl = """
%s

Issues

%s
"""

    vuln_without_tpl = """
There were found URL without CSP. Please, review it:

    %s
"""

    vuln_no_csp_tpl = """
The whole target has no CSP protection.
"""
    common_tpl = """
Common CSP related issues:

%s
"""
