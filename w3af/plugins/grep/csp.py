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
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.csp.utils import find_vulns


class csp(GrepPlugin):
    """
    Identifies incorrect or too permissive Content Security Policy headers.
    """
    VULN_NAME = 'CSP vulnerability'

    def __init__(self):
        """
        Class init
        """
        GrepPlugin.__init__(self)

        self._total_count = 0
        self._vulns = DiskList(table_prefix='csp')
        self._urls = ScalableBloomFilter()
                
    def get_long_desc(self):
        return """
        This plugin identifies incorrect or too permissive CSP (Content Security Policy)
        headers returned by the web application under analysis.

        Additional information: 
         * https://www.owasp.org/index.php/Content_Security_Policy
         * http://www.w3.org/TR/CSP
        """        

    def grep(self, request, response):
        """
        Perform search on current HTTP request/response exchange.
        Store information about vulns for further global processing.
        
        @param request: HTTP request
        @param response: HTTP response  
        """
        # Check that current URL has not been already analyzed
        response_url = response.get_url().uri2url()
        if response_url in self._urls:
            return        

        self._urls.add(response_url)
                
        # Search issues using dedicated module
        csp_vulns = find_vulns(response)
        
        # Analyze issue list
        if len(csp_vulns) > 0:
            vuln_store_item = DiskCSPVulnStoreItem(response_url,
                                                   response.id,
                                                   csp_vulns)
            self._vulns.append(vuln_store_item)

            # Increment the vulnerabilities counter
            for csp_directive_name in csp_vulns:
                self._total_count += len(csp_vulns[csp_directive_name])
                
    def end(self):
        """
        Perform global analysis for all vulnerabilities found.
        """
        # Check if vulns have been found
        if self._total_count == 0:
            return
        
        # Parse vulns collection
        vuln_already_reported = []

        for vuln_store_item in self._vulns:
            for csp_directive_name, csp_vulns_list in vuln_store_item.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:
                    # Check if the current vuln is common (shared) to several
                    # url processed and has been already reported
                    if csp_vuln.desc in vuln_already_reported:
                        continue

                    # Search for current vuln occurrences in order to know if
                    # the vuln is common (shared) to several url processed
                    occurrences = self._find_occurrences(csp_vuln.desc)

                    if len(occurrences) > 1:
                        # Shared vuln case
                        v = Vuln(self.VULN_NAME, csp_vuln.desc,
                                 csp_vuln.severity, occurrences,
                                 self.get_name())
                        v.set_url(vuln_store_item.url.base_url())

                        vuln_already_reported.append(csp_vuln.desc)
                    else:
                        # Isolated vuln case
                        v = Vuln(self.VULN_NAME, csp_vuln.desc,
                                 csp_vuln.severity, vuln_store_item.resp_id,
                                 self.get_name())
                        v.set_url(vuln_store_item.url)

                    # Report vuln
                    self.kb_append(self, 'csp', v)
                
        # Cleanup
        self._vulns.cleanup()

    def _find_occurrences(self, vuln_desc):
        """
        Internal utility function to find all occurrences of a vuln
        into the global collection of vulns found by the plugin.
        
        @param vuln_desc: Vulnerability description.
        @return: List of response ID for which the vuln is found.
        """
        list_resp_id = []

        # Check input for quick exit
        if vuln_desc is None or vuln_desc.strip() == "":
            return list_resp_id
       
        # Parse vulns collection
        ref = vuln_desc.lower().strip()        
        for vuln_store_item in self._vulns:
            for csp_directive_name, csp_vulns_list in vuln_store_item.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:        
                    if csp_vuln.desc.strip().lower() == ref:
                        if vuln_store_item.resp_id not in list_resp_id:
                            list_resp_id.append(vuln_store_item.resp_id)

        return list_resp_id


class DiskCSPVulnStoreItem(DiskItem):
    """
    This is a class to store CSP vulnerabilities found for a URL (URL+ID) in a
    DiskList or DiskSet.
    """

    def __init__(self, r_url, r_id, r_vulns):
        """
        Constructor.
        @param r_url: HTTP response url
        @param r_id: HTTP response ID
        @param r_vulns: CSP vulnerabilities found
        """
        self.url = r_url
        self.resp_id = r_id
        self.csp_vulns = r_vulns

    def get_eq_attrs(self):
        """
        Implements method from base class.
        """
        return ['url', 'resp_id']
