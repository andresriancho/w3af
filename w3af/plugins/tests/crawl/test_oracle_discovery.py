"""
test_oracle_discovery.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http


class TestOracleDiscovery(PluginTest):

    base_url = get_moth_http()

    _run_config = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('oracle_discovery'),)}
    }

    def test_oracle_discovery(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        infos = self.kb.get('oracle_discovery', 'oracle_discovery')
        self.assertEqual(len(infos), 1, infos)

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertIn(self.base_url + 'portal/page', urls)
