'''
test_dirbruter.py

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
from nose.plugins.skip import Skip, SkipTest


class TestDirBruter(PluginTest):
    
    base_url = 'http://moth/'
    
    _run_config = {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('dir_bruter',
                                                   ('be_recursive', False, PluginConfig.BOOL)
                                                   ),)}
        }
    
    def test_fuzzer_found_urls(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])
        urls = self.kb.getData('urls', 'url_objects')
        
        EXPECTED_URLS = ('setup/', 'header/', 'images/', 'portal/', 'index/')        
        
        self.assertEquals(
                set(str(u) for u in urls),
                set((self.base_url + end) for end in EXPECTED_URLS),
                urls
                )
    
    def test_no_index(self):
        raise SkipTest('FIXME: The index/ in EXPECTED_URLS is a bug!')
    
    def test_recursive(self):
        raise SkipTest('FIXME: Need to add test case with recursive flag on.')
        