'''
test_archive_dot_org.py

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
from core.controllers.w3afException import w3afRunOnce

from core.data.parsers.urlParser import url_object
from core.data.request.fuzzable_request import fuzzable_request
from core.data.url.xUrllib import xUrllib

from plugins.crawl.archive_dot_org import archive_dot_org
from plugins.tests.helper import PluginTest, PluginConfig


class TestArchiveDotOrg(PluginTest):
    
    archive_url = 'http://w3af.sourceforge.net/'
    
    _run_config = {
            'target': None,
            'plugins': {'crawl': (PluginConfig('archive_dot_org',),)}
        }
    
    
    def test_found_urls(self):
        self._scan(self.archive_url, self._run_config['plugins'])
        urls = self.kb.getData('urls', 'url_objects')
        
        EXPECTED_URLS = ('oss.php', 'objectives.php', 'plugin-descriptions.php',
                         'videos/video-demos.php', 'videos/w3af-vs-wivet/w3af-vs-wivet.htm', 
                         'documentation/epydoc/core.data.kb-module.html')        
        
        expected_set = set((self.archive_url + end) for end in EXPECTED_URLS)
        urls_as_strings = set([u.url_string for u in urls])
        
        self.assertTrue( urls_as_strings.issuperset(expected_set) )
        self.assertGreater(len(urls), 50)
    
    def test_raise_on_local_domain(self):
        url = url_object('http://moth/')
        fr = fuzzable_request(url, method='GET')
        ado = archive_dot_org()
        self.assertRaises(w3afRunOnce, ado.crawl_wrapper, fr)

    def test_raise_on_domain_not_in_archive(self):
        url = url_object('http://www.w3af.org/')
        fr = fuzzable_request(url, method='GET')
        
        ado = archive_dot_org()
        uri_opener = xUrllib()
        ado.set_url_opener( uri_opener )
        
        self.assertRaises(w3afRunOnce, ado.crawl_wrapper, fr)