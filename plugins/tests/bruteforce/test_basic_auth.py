'''
test_basic_auth.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

from ..helper import PluginTest, PluginConfig

class TestBasicAuth(PluginTest):
    
    target_url_easy = 'http://moth/w3af/bruteforce/basic_auth/easy_guess/'
    target_url_impossible = 'http://moth/w3af/bruteforce/basic_auth/impossible_guess/'
    
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                 'bruteforce': (PluginConfig('basic_auth'),),
                 'grep': (PluginConfig('http_auth_detect'),),
                 }
            }
        }
    
    def test_found_credentials(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan( self.target_url_easy , cfg['plugins'])

        # Assert the general results
        vulns = self.kb.getData('basic_auth', 'auth')
        self.assertEquals(len(vulns), 1)
        
        vuln = vulns[0]
        
        self.assertEquals(vuln.getName(), 'Guessable credentials')

        self.assertEquals(vuln.getURL().url_string, self.target_url_easy)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], 'admin')
        
    def test_not_found_credentials(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan( self.target_url_impossible , cfg['plugins'])

        # Assert the general results
        vulns = self.kb.getData('basic_auth', 'auth')
        self.assertEquals(len(vulns), 0)
