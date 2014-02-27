# coding: utf8
"""
test_wordnet.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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
"""
import w3af.core.data.kb.knowledge_base as kb

from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.crawl.wordnet import wordnet


class TestWordnet(PluginTest):

    target_url = get_moth_http('/crawl/wordnet/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                        'crawl': (PluginConfig('wordnet',
                                               ('wn_results', 20, PluginConfig.INT)),
                                  PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL)))
            },
        }
    }

    @attr('ci_fails')
    def test_found_urls(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        expected_urls = (
                         '', 'azure.html', 'blue.html', 'green.html', 'hide.py',
                         'red.html', 'show.py', 'show.py?os=linux',
                         'show.py?os=unix', 'show.py?os=windows',
        )

        frs = kb.kb.get_all_known_fuzzable_requests()
        
        self.assertEquals(
            set(fr.get_uri().url_string for fr in frs),
            set((self.target_url + end) for end in expected_urls)
        )

    def test_search_wordnet(self):
        wn = wordnet()
        wn_result = wn._search_wn('blue')
        
        self.assertEqual(len(wn_result), wn._wordnet_results)
        self.assertIn('red', wn_result)