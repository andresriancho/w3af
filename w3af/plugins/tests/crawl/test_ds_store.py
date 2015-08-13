"""
test_ds_store.py

Copyright 2015 Andres Riancho

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
from os.path import join

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestDSStore(PluginTest):

    target_url = 'http://mock/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('ds_store'),)}
        }
    }

    DS_STORE = join(ROOT_PATH, 'core/data/parsers/doc/tests/data/DS_Store-2')

    MOCK_RESPONSES = [MockResponse('/.DS_Store', file(DS_STORE).read()),
                      MockResponse('/priv', 'Private directory hidden')]

    def test_find_priv_directory(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('ds_store', 'ds_store')
        self.assertEqual(len(infos), 1)

        info = infos[0]
        self.assertEqual(info.get_name(), '.DS_Store file found')

        expected_urls = ('', 'priv', '.DS_Store')
        urls = self.kb.get_all_known_urls()

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.target_url + end) for end in expected_urls)
        )