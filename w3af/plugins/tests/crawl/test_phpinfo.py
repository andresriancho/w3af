"""
test_phpinfo.py

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


class TestPHPInfo516(PluginTest):

    target_url = 'http://httpretty/'

    PHPINFO = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'phpinfo', 'phpinfo-5.1.6.html')

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='index home page',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/phpversion.php',
                                   body=file(PHPINFO).read(),
                                   method='GET',
                                   status=200),
                      ]

    _run_config = {
        'target': target_url,
        'plugins': {'crawl': (PluginConfig('phpinfo'),)}
    }

    def test_phpinfo(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertIn(self.target_url + 'phpversion.php', urls)

        infos = self.kb.get('phpinfo', 'phpinfo')
        self.assertTrue(len(infos) > 5, infos)

        info_urls = [i.get_url().url_string for i in infos]
        self.assertIn(self.target_url + 'phpversion.php', info_urls)
        
        found_infos = set([i.get_name() for i in infos])

        expected_infos = {'PHP register_globals: On',
                          'PHP expose_php: On',
                          'PHP session.hash_function:md5',
                          'phpinfo() file found'}

        for expected_info in expected_infos:
            self.assertIn(expected_info, found_infos)


class TestPHPInfo4311(TestPHPInfo516):
    PHPINFO = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'phpinfo', 'phpinfo-4.3.11.html')


class TestPHPInfo513rc4dev(TestPHPInfo516):
    PHPINFO = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'phpinfo', 'phpinfo-5.1.3-rc4dev.html')


class TestPHPInfo433(TestPHPInfo516):
    PHPINFO = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'phpinfo', 'phpinfo-4.3.3.html')
