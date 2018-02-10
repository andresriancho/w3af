"""
test_dot_listing.py

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
import os

from w3af import ROOT_PATH

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.crawl.dot_listing import dot_listing


class TestDotListing(PluginTest):

    target_url = 'http://mock'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('dot_listing'),)}
        }
    }

    DOT_LISTING = file(os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'dot_listing', 'listing_test_1.txt')).read()

    MOCK_RESPONSES = [MockResponse('http://mock/.listing', DOT_LISTING),
                      MockResponse('http://mock/wasadhiya-7.mp3', 'Secret file'),
                      MockResponse('http://mock/', 'Not here', status=404)]

    def test_dot_listing(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dot_listing', 'dot_listing')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual(info.get_name(), '.listing file found')

        expected_urls = ('/', '/.listing', '/wasadhiya-7.mp3')
        urls = self.kb.get_all_known_urls()

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.target_url + end) for end in expected_urls)
        )

    def test_listing_extraction(self):
        listing_files_path = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'dot_listing')
        file_name_fmt = 'listing_test_%s.txt'

        dot_listing_inst = dot_listing()

        users = set()
        groups = set()
        files = set()

        for i in xrange(1, 4):
            file_name = file_name_fmt % i
            file_path = os.path.join(listing_files_path, file_name)
            file_content = file(file_path).read()
            for user, group, filename in dot_listing_inst._extract_info_from_listing(file_content):
                users.add(user)
                groups.add(group)
                files.add(filename)

        self.assertGreater(len(files), 20)

        self.assertTrue('stepstolife' in users)
        self.assertTrue('1193040' in users)

        self.assertTrue('1000007' in groups)
        self.assertTrue('psaserv' in groups)

        self.assertTrue('_vti_cnf.exe' in files)
        self.assertTrue('salvage_2.html' in files)
        self.assertTrue('GodRest.mid' in files)
