'''
test_phpinfo.py

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

class TestPHPInfo(PluginTest):
    
    base_url = 'https://moth/'
    
    _run_config = {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('phpinfo'),)}
        }
    
    def test_phpinfo(self):
        self._scan( self._run_config['target'], self._run_config['plugins'] )
        
        urls = self.kb.getData('urls', 'url_objects')
        urls = [ url.url_string for url in urls ]
        
        self.assertTrue( self.base_url + 'phpinfo.php' in urls )
        
        
        infos = self.kb.getData('phpinfo', 'phpinfo')
        self.assertTrue( len(infos) > 5, infos)
        
        EXPECTED_INFOS = (
                          'register_globals: Off',
                          'expose_php: On',
                          'session.hash_function:md5',
                         )
        
        info_urls = [ i.getURL().url_string for i in infos ]
        self.assertTrue( self.base_url + 'phpinfo.php' in info_urls )
        
        for e_info_name in EXPECTED_INFOS:
            for info in infos:
                if info.getName() == e_info_name:
                    break
            else:
                self.assertTrue(False, e_info_name)
        
