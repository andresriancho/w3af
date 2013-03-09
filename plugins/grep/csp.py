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
import msgpack

from core.data.db.disk_list import DiskList
from core.data.kb.vuln import Vuln
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.csp.utils import find_vulns, CSPVulnerability 
from collections import namedtuple

#Define NamedTuple tuple subclass to store a CSP vulnerabilities with response context informations.        
#See link below to know why I placed the definition outside the class:
#http://stackoverflow.com/questions/4677012/python-cant-pickle-type-x-attribute-lookup-failed
CSPVulnStore = namedtuple('CSPVulnStore', ['url', 'resp_id', 'csp_vulns']) 

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

    def _cspvulnstore_to_string(self, cspvulnstore):
        '''
        Internal utility method to serialize a CSPVulnStore instance 
        to a string.

        @param cspvulnstore: CSPVulnStore instance to serialize
        @return: Instance serialized as string
        '''
        return msgpack.packb(cspvulnstore)

    def _string_to_cspvulnstore(self, string):
        '''
        Internal utility method to deserialize a string to a 
        CSPVulnStore instance.        

        Note: MsgPack serialization break the sub NamedTuple structure
        then we must rebuild it...

        @param string: String to deserialize
        @return: CSPVulnStore instance        
        '''
        #Deserialize
        tuple_data = msgpack.unpackb(string)       
        #Access data and rebuild NamedTuple structure
        ##Access data
        response_url = tuple_data[0]
        response_id = tuple_data[1]
        csp_vulns =tuple_data[2]
        ##Rebuild sub NamedTuple structure
        vulns_dict_by_directive = {}
        for csp_directive_name, csp_vulns_list in csp_vulns.iteritems():
            if csp_directive_name not in vulns_dict_by_directive:
                vulns_dict_by_directive[csp_directive_name] = []
            vulns_details_list = vulns_dict_by_directive[csp_directive_name]
            for csp_vuln in csp_vulns_list: 
                v = CSPVulnerability(csp_vuln[0],csp_vuln[1])   
                vulns_details_list.append(v)
            vulns_dict_by_directive[csp_directive_name] = vulns_details_list

        return CSPVulnStore(response_url, response_id, vulns_dict_by_directive)
                
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
        @param response: HTP response  
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
            #Store for a URL the triplet:
            # Response URL
            # Response ID            
            # Dictionary of CSP vulnerabilities
            vuln_store = CSPVulnStore(response_url, response.id, csp_vulns)   
            vuln_store_serialized = self._cspvulnstore_to_string(vuln_store)
            self._vulns.append(vuln_store_serialized)
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
        for vuln_store_serialized in self._vulns:
            vuln_store_deserialized = self._string_to_cspvulnstore(vuln_store_serialized)
            for csp_directive_name, csp_vulns_list in vuln_store_deserialized.csp_vulns.iteritems():
                for csp_vuln in csp_vulns_list:
                    desc = "[CSP Directive '" + csp_directive_name + "'] : " + csp_vuln.desc
                    v = Vuln('CSP vulnerability', desc,
                             csp_vuln.severity, vuln_store_deserialized.resp_id, self.get_name())
                    self.kb_append(self, 'csp', v)  
                
        #Cleanup
        self._urls.cleanup()
        self._vulns.cleanup()