'''
test_webspider.py

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

class TestWebSpider(PluginTest):
    
    follow_links_url = 'http://moth/w3af/discovery/web_spider/follow_links/'
    dir_get_url = 'http://moth/w3af/discovery/web_spider/a/b/c/d/'
    
    
    _run_configs = {
        'cfg1': {'target': follow_links_url + '1.html',
                 'plugins': (
                    PluginConfig('discovery.webSpider',
                         ('onlyForward', True, PluginConfig.BOOL)),
                     )
                 },
        'cfg2': {'target': dir_get_url,
                 'plugins': (
                    PluginConfig('discovery.webSpider',
                         ('onlyForward', True, PluginConfig.BOOL)),
                    PluginConfig('discovery.allowedMethods')
                    ),
                 },
    }
    
    def test_spider_found_urls(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        expected_urls = (
             '3.html', '4.html', '',
             'd%20f/index.html', '2.html', 'a%20b.html',
             'a.gif', 'd%20f/', '1.html'
             )
        urls = self.kb.getData('urls', 'urlList')
        self.assertEquals(
                set(str(u) for u in urls),
                set((self.follow_links_url + end) for end in expected_urls)
                )