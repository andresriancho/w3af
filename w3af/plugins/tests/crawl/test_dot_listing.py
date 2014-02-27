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

from nose.plugins.attrib import attr
from w3af import ROOT_PATH

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.crawl.dot_listing import dot_listing


class TestDotListing(PluginTest):

    base_url = 'https://moth/w3af/crawl/dot_listing/'

    _run_config = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('dot_listing'),)}
    }

    @attr('ci_fails')
    def test_dot_listing(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        infos = self.kb.get('dot_listing', 'dot_listing')
        self.assertEqual(len(infos), 2)

        self.assertEqual(
            set(['.listing file found',
                'Operating system username and group leak']),
            set([i.get_name() for i in infos]))
        self.assertEqual(set([self.base_url + '.listing'] * 2),
                         set([i.get_url().url_string for i in infos]))

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertTrue(self.base_url + '.listing' in urls)
        self.assertTrue(self.base_url + 'hidden.txt' in urls)

    def test_listing_extraction(self):
        listing_files_path = os.path.join(ROOT_PATH, 'plugins', 'tests',
                                          'crawl', 'dot_listing')
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