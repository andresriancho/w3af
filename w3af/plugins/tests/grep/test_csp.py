"""
test_csp.py
 
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
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
 
 
@attr('ci_ready')
class TestCSP(PluginTest):
 
    # Test scripts URLs
    base_url = get_moth_http()
    csp_with_error_url = base_url + '/grep/csp/index.php'    
    csp_without_error_url = base_url + '/grep/csp/csp_without_error.php'

    #Test configurations 
    _run_configs = {          
        'cfg_with_error': {
            'target': csp_with_error_url,
            'plugins': {
                'grep': (PluginConfig('csp'),),
                'crawl': (
                    PluginConfig('web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        },        
        'cfg_without_error': {
            'target': csp_without_error_url,
            'plugins': {
                'grep': (PluginConfig('csp'),)
            }
        }
    }

    def test_found_vuln(self):
        """
        Test to validate case in which error are found:
        One vuln is common to several pages and others are isoled.
        """
        #Prepare expectation
        expected_vulns_desc = []
        #---This vuln is shared by several pages
        expected_vulns_desc.append("Directive 'default-src' allow all sources.")
        #---Theses vulns are isolated
        expected_vulns_desc.append("Directive 'script-src' allow all javascript sources.")
        expected_vulns_desc.append("Directive 'script-src' is defined but no directive 'script-nonce' is defined to protect javascript resources.")
        expected_vulns_desc.append("Directive 'object-src' allow all plugin sources.")
        expected_vulns_desc.append("Somes directives are misspelled: def-src,sript-src.")

        #Configure and run test case
        cfg = self._run_configs['cfg_with_error']
        self._scan(cfg['target'], cfg['plugins'])

        #Apply validation
        vulns = self.kb.get('csp', 'csp')
        self.assertEquals(len(expected_vulns_desc), len(vulns))        
        counter = 0
        for v in vulns:
            if v.get_desc(False) in expected_vulns_desc:
                counter += 1
        self.assertEquals(counter, len(expected_vulns_desc))        

    def test_no_vuln(self):
        """
        Test to validate case in which no error is found.
        """
        #Configure and run test case
        cfg = self._run_configs['cfg_without_error']
        self._scan(cfg['target'], cfg['plugins'])
        
        #Apply validation
        vulns = self.kb.get('csp', 'csp')
        self.assertEquals(0, len(vulns))        