"""
test_dwsync_xml.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestDWSyncXML(PluginTest):

    target_url = 'http://mock'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('dwsync_xml'),)}
        }
    }

    DWSYNC = ('<dwsync>'
              '    <file name="/secret/" server="sitename.com/www/"'
              '          local="129063550024489121"'
              '          remote="129063549600000000" />'
              '</dwsync>')

    MOCK_RESPONSES = [MockResponse('http://mock/_notes/dwsync.xml', DWSYNC),
                      MockResponse('http://mock/secret/', 'Secret directory')]

    def test_dwsync_xml(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dwsync_xml', 'dwsync_xml')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual(info.get_name(), 'dwsync.xml file found')

        expected_urls = ('/', '/_notes/dwsync.xml', '/secret/')
        urls = self.kb.get_all_known_urls()

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.target_url + end) for end in expected_urls)
        )

