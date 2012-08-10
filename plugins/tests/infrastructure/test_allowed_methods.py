'''
test_allowed_methods.py

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

class Testallowed_methods(PluginTest):
    
    modsecurity_url = 'http://modsecurity/'
    moth_url = 'http://moth/'
    
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('allowed_methods'),)}
            }
        }
    
    def test_moth(self):
        '''
        Test the "default" configuration for Apache+PHP.
        '''
        cfg = self._run_configs['cfg']
        self._scan(self.moth_url, cfg['plugins'])
        
        infos = self.kb.getData('allowed_methods', 'custom-configuration')
        
        self.assertEqual( len(infos), 1, infos )
        
        info = infos[0]
        
        msg = 'The remote Web server has a custom configuration, in which any'
        msg += ' non existent'
        self.assertTrue( info.getDesc().startswith(msg))
        self.assertEqual( info.getName(), 'Non existent methods default to GET')
        
    def test_modsecurity(self):
        '''
        Test a different configuration:
            RewriteEngine on
            RewriteCond %{THE_REQUEST} !^(POST|GET)\ /.*\ HTTP/1\.1$
            RewriteRule .* - [F]
        '''
        cfg = self._run_configs['cfg']
        self._scan(self.modsecurity_url, cfg['plugins'])
        
        infos = self.kb.getData('allowed_methods', 'custom-configuration')

        self.assertEqual( len(infos), 0, infos )
        
        