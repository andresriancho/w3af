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
        Store informations about vulns for futher global processing.
        
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
        #TODO perform more deeper analysis in order find vulns correlation !!!
        for vuln_store_item in self._vulns:
            for csp_directive_name, csp_vulns_list in vuln_store_item.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:
                    desc = "[CSP Directive '" + csp_directive_name + "'] : " + csp_vuln.desc
                    v = Vuln('CSP vulnerability', desc,
                             csp_vuln.severity, vuln_store_item.resp_id, self.get_name())
                    self.kb_append(self, 'csp', v)  
                
        #Cleanup
        self._urls.cleanup()
        self._vulns.cleanup()