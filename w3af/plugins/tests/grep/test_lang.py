"""
test_lang.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestLang(PluginTest):

    langs_url = get_moth_http('/grep/lang/%s.html')

    _run_configs = {
        'direct': {
            'target': None,
            'plugins': {
                'grep': (PluginConfig('lang'),),
            }
        },

        'crawl': {
            'target': get_moth_http('/grep/'),
            'plugins': {
                'grep': (PluginConfig('lang'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_id_es(self):
        cfg = self._run_configs['direct']
        self._scan(self.langs_url % 'es', cfg['plugins'])

        lang = self.kb.raw_read('lang', 'lang')
        self.assertEquals('es', lang)

    def test_id_en(self):
        cfg = self._run_configs['direct']
        self._scan(self.langs_url % 'en', cfg['plugins'])

        lang = self.kb.raw_read('lang', 'lang')
        self.assertEquals('en', lang)

    def test_id_en_crawl(self):
        cfg = self._run_configs['crawl']
        self._scan(self.langs_url % 'en', cfg['plugins'])
        
        lang = self.kb.raw_read('lang', 'lang')
        self.assertEquals('en', lang)
