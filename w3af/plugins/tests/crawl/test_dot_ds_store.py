"""
test_ds_store.py

Copyright 2018 Andres Riancho

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
import os

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af import ROOT_PATH


class TestDSStore(PluginTest):

    target_url = 'http://mock'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('dot_ds_store'),)}
        }
    }

    DS_STORE = file(os.path.join(ROOT_PATH, 'plugins/tests/crawl/ds_store/DS_Store')).read()

    MOCK_RESPONSES = [MockResponse('http://mock/.DS_Store', DS_STORE),
                      MockResponse('http://mock/other', 'Secret directory'),
                      MockResponse('http://mock/', 'Not here', status=404)]

    def test_ds_store(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dot_ds_store', 'dot_ds_store')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual(info.get_name(), '.DS_Store file found')

        expected_urls = ('/', '/.DS_Store', '/other')
        urls = self.kb.get_all_known_urls()

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.target_url + end) for end in expected_urls)
        )
