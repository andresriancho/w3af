'''
test_digitsum.py

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


class TestDigitSum(PluginTest):
    
    qs_url = 'http://moth/w3af/discovery/digitSum/index1.php?id=22'
    fname_url = 'http://moth/w3af/discovery/digitSum/index-3-1.html'
    
    _run_config = {
            'target': None,
            'plugins': {'discovery': (PluginConfig('digitSum',),)}
        }
    
    def test_found_fname(self):
        self._scan(self.fname_url, self._run_config['plugins'])
        urls = self.kb.getData('urls', 'url_objects')
        
        EXPECTED_URLS = ('index-3-1.html', 'index-2-1.html', '')        
        
        self.assertEquals(
                set(str(u) for u in urls),
                set((self.fname_url + end) for end in EXPECTED_URLS),
                urls
                )
    
    def test_found_qs(self):
        self._scan(self.fname_url, self._run_config['plugins'])
        urls = self.kb.getData('urls', 'url_objects')
        
        EXPECTED_URLS = ('index1.php?id=22', 'index1.php?id=21', '')        
        
        self.assertEquals(
                set(str(u) for u in urls),
                set((self.qs_url + end) for end in EXPECTED_URLS),
                urls
                )
        