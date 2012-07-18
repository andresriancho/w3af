'''
test_find_git.py

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


class TestFindGit(PluginTest):
    
    base_url = 'http://moth/w3af/discovery/find_git/'
    
    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('find_git'),)}
            }
        }
    
    def test_fuzzer_user(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        vulns = self.kb.getData('find_git', 'GIT')
        
        self.assertEqual( len(vulns), 1, vulns )
        
        vuln = vulns[0]
        
        self.assertEquals( vuln.getName(), 'Possible Git repository found' )
        self.assertEquals( vuln.getURL().url_string, self.base_url + '.git/HEAD' )
        

