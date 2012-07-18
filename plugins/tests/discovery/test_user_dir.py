'''
test_user_dir.py

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


class TestUserDir(PluginTest):
    
    base_url = 'http://moth/w3af/'
    
    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('user_dir'),)}
            }
        }
    
    def test_fuzzer_user(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        users = self.kb.getData('user_dir', 'users')
        
        self.assertEqual( len(users), 1, users )
        
        user = users[0]
        
        self.assertTrue( user.getName().startswith('User directory:') )
        self.assertEquals( user.getURL().url_string, 'http://moth/~www/' )
        

