'''
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
'''
 
from plugins.tests.helper import PluginTest, PluginConfig
import core.data.constants.severity as severity
 
 
class TestCSP(PluginTest):
 
    #Test scripts URLs
    context_root = 'localhost:81'
    csp_with_error_url = 'http://' + context_root + '/grep/csp_with_error.php'    
    csp_without_error_url = 'http://' + context_root + '/grep/csp_without_error.php'

    #Test configurations 
    _run_configs = {
        'cfg_with_error': {
            'target': csp_with_error_url,
            'plugins': {
                'grep': (PluginConfig('csp'),)
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
        cfg = self._run_configs['cfg_with_error']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('csp', 'csp')
        self.assertEquals(4, len(vulns))


    def test_no_vuln(self):
        cfg = self._run_configs['cfg_without_error']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('csp', 'csp')
        self.assertEquals(0, len(vulns))        