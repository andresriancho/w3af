'''
test_form_auth.py

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

class TestFormAuth(PluginTest):
    
    target_url = 'http://moth/w3af/bruteforce/form_login/with_post.html'
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                 'bruteforce': (PluginConfig('form_auth'),),
                 'discovery': (
                      PluginConfig(
                          'web_spider',
                          ('onlyForward', True, PluginConfig.BOOL)),
                  )
                 }
            }
        }
    
    def test_found_credentials(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.getData('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)
        
        vuln = vulns[0]
        
        self.assertEquals(vuln.getName(), 'Guessable credentials')
        vuln_url = 'http://moth/w3af/bruteforce/form_login/dataReceptor.php'
        self.assertEquals(vuln.getURL().url_string, vuln_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], '1234')
        
