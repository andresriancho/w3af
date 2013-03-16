'''
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

'''
import core.data.constants.severity as severity

from core.data.db.disk_list import DiskList
from core.data.db.disk_csp_vuln_store_item import DiskCSPVulnStoreItem
from core.data.kb.vuln import Vuln
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.csp.utils import find_vulns

class csp(GrepPlugin):
    '''
    Find in each page vulnerabilities coming from Content Security Policy  
    (W3C specification) bad or too permissive configuration.    
    '''

    def __init__(self):
        '''
        Class init
        '''
        GrepPlugin.__init__(self)

        self._total_count = 0
        self._vulns = DiskList()
        self._urls = DiskList() 
                
    def get_long_desc(self):
        return '''
        This plugin find, in each page, vulnerabilities coming from 
        Content Security Policy (W3C specification) bad or too permissive 
        configuration.

        Additional information: 
        https://www.owasp.org/index.php/Content_Security_Policy
        http://www.w3.org/TR/CSP
        '''        

    def grep(self, request, response):
        '''
        Perform search on current HTTP request/response exchange.
        Store informations about vulns for further global processing.
        
        @param request: HTTP request
        @param response: HTTP response  
        '''
        #Check that current URL has not been already analyzed
        response_url = str(response.get_url().uri2url())
        if response_url in self._urls:
            return        
        else:
            self._urls.append(response_url)    
                
        #Search issues using dedicated module
        csp_vulns = find_vulns(response)
        
        #Analyze issue list
        if len(csp_vulns) > 0:
            vuln_store_item = DiskCSPVulnStoreItem(response_url, response.id, csp_vulns)   
            self._vulns.append(vuln_store_item)
            #Increment the vulnerabilities counter 
            for csp_directive_name in csp_vulns:
                self._total_count += len(csp_vulns[csp_directive_name])
                
    def end(self):
        '''
        Perform global analysis for all vulnerabilities found.
        '''
        #Check if vulns has been found
        if self._total_count == 0:
            return
        
        #Parse vulns collection
        vuln_already_reported = []
        total_url_processed_count = len(self._urls)
        for vuln_store_item in self._vulns:
            for csp_directive_name, csp_vulns_list in vuln_store_item.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:
                    #Check if the current vuln is common (shared) to several url processed 
                    #and have been already reported
                    if csp_vuln.desc in vuln_already_reported:
                        continue
                    #Search for current vuln occurences in order to know if 
                    #the vuln is common (shared) to several url processed                                    
                    occurences = self._find_occurences(csp_vuln.desc)
                    v = None
                    if len(occurences) > 1:
                        #Shared vuln case
                        v = Vuln('CSP vulnerability', csp_vuln.desc,
                            csp_vuln.severity, occurences, self.get_name())
                        vuln_already_reported.append(csp_vuln.desc)
                    else:
                        #Isolated vuln case
                        v = Vuln('CSP vulnerability', csp_vuln.desc,
                            csp_vuln.severity, vuln_store_item.resp_id, self.get_name())
                    #Report vuln
                    self.kb_append(self, 'csp', v)
                
        #Cleanup
        self._urls.cleanup()
        self._vulns.cleanup()


    def _find_occurences(self, vuln_desc):
        '''
        Internal utility function to find all occurences of a vuln 
        into the global collection of vulns found by the plugin.
        
        @param vuln_desc: Vulnerability description.
        @return: List of response ID for which the vuln is found.
        '''
        list_resp_id = []

        #Check input for quick exit
        if vuln_desc is None or vuln_desc.strip() == "":
            return list_resp_id
       
        #Parse vulns collection
        ref = vuln_desc.lower().strip()        
        for vuln_store_item in self._vulns:
            for csp_directive_name, csp_vulns_list in vuln_store_item.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:        
                    if csp_vuln.desc.strip().lower() == ref:
                        if vuln_store_item.resp_id  not in list_resp_id:
                            list_resp_id.append(vuln_store_item.resp_id)

        return list_resp_id