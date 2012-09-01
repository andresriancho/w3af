# coding: utf8
'''
test_wordnet.py

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

class TestWordnet(PluginTest):
    
    target_url = 'http://moth/w3af/crawl/wordnet/'
        
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                        'crawl': (PluginConfig('wordnet',
                                         ('wn_results', 20, PluginConfig.INT)),
                                      PluginConfig('web_spider',
                                         ('onlyForward', True, PluginConfig.BOOL)))
                        },
                }
    }
    
    def test_found_urls(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        expected_urls = (
             'azure.html', 'blue.html', 'green.html', 'red.html',
             'hide.php', 'show.php', '',
             )
        
        urls = self.kb.get('urls', 'url_objects')
        self.assertEquals(
                set(str(u) for u in urls),
                set((self.target_url + end) for end in expected_urls)
                )
    
    def test_fix_bug(self):
        '''
         FIXME: There is an ugly bug in the wordnet plugin that returns many
         URIs to the core. Example:
        - http://moth/w3af/crawl/wordnet/hide.php | Method: GET | Parameters: (os="bay window")
        - http://moth/w3af/crawl/wordnet/hide.php | Method: GET | Parameters: (os="car window")
        - http://moth/w3af/crawl/wordnet/hide.php | Method: GET | Parameters: (os="casement w...")
        - http://moth/w3af/crawl/wordnet/hide.php | Method: GET | Parameters: (os="clerestory")
        '''
        self.assertTrue(False)

