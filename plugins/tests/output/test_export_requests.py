# coding: utf8
'''
test_export_requests.py

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

import os
import urllib
from ..helper import PluginTest, PluginConfig
from core.data.parsers.urlParser import url_object


class TestExportRequests(PluginTest):
    
    follow_links_url = 'http://moth/w3af/discovery/web_spider/follow_links/1.html'
    
    _run_configs = {
        'cfg': {
            'target': follow_links_url,
            'plugins': {
                'discovery': (
                    PluginConfig('webSpider',
                             ('onlyForward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig('export_requests',
                             ('output_file', 'output-fr.csv', PluginConfig.STR)),
                )
             }
         },
    }
    
    def test_export_requests(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        urls = self.kb.getData('urls', 'url_objects')
        freq = self.kb.getData('urls', 'fuzzable_requests')

        self.assertTrue(os.path.exists('output-fr.csv'))
        
        file_urls = self._get_urls_from_file()
        
        self.assertEquals(
                set(sorted(file_urls)),
                set(sorted(urls))
                )
        
        self.assertEquals(
                set(sorted(file_urls)),
                set(sorted([fr.getURL() for fr in freq]))
                )        
    
    def _get_urls_from_file(self):
        # Get the contents of the output file
        file_urls = []
        for line in file('output-fr.csv'):
            if 'http' not in line:
                continue
            else:
                url_str = line.split(',')[1]
                url_str = urllib.unquote(url_str)
                url = url_object(url_str)
                file_urls.append(url)
        return file_urls
    
    def tearDown(self):
        super(TestExportRequests, self).tearDown()
        try:
            os.remove('output-fr.csv')
        except:
            pass
    
