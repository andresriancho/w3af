'''
test_dirbruter.py

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
'''
import os
import shutil

from plugins.tests.helper import PluginTest, PluginConfig
from nose.plugins.skip import SkipTest


class TestDirBruter(PluginTest):

    directory_url = 'http://moth/w3af/crawl/dir_bruter/'
    base_url = 'http://moth/'

    _run_simple = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('dir_bruter',
                                           ('be_recursive',
                                            False,
                                            PluginConfig.BOOL)
                                           ),)}
    }

    _run_recursive = {
        'target': directory_url,
        'plugins': {'crawl': (PluginConfig('dir_bruter',
                                           ('be_recursive',
                                            True,
                                            PluginConfig.BOOL)
                                           ),)}
    }

    TEST_DB_PATH = os.path.join(
        'plugins', 'tests', 'crawl', 'dir_bruter', 'test_dirs_small.db')
    DIST_DB_PATH = os.path.join(
        'plugins', 'crawl', 'dir_bruter', 'common_dirs_small.db')
    TEMP_DB_PATH = os.path.join('plugins', 'tests', 'crawl',
                                'dir_bruter', 'common_dirs_small.db.orig')

    def setUp(self):
        '''
        This is a rather complex setUp since I need to move the failing_spider.py
        plugin to the plugin directory in order to be able to run it afterwards.

        In the tearDown method, I'll remove the file.
        '''
        shutil.move(self.DIST_DB_PATH, self.TEMP_DB_PATH)
        shutil.copy(self.TEST_DB_PATH, self.DIST_DB_PATH)

        super(TestDirBruter, self).setUp()

    def tearDown(self):
        shutil.move(self.TEMP_DB_PATH, self.DIST_DB_PATH)

        super(TestDirBruter, self).tearDown()

    def test_fuzzer_found_urls(self):
        self._scan(self._run_simple['target'], self._run_simple['plugins'])
        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = (
            'setup/', 'header/', 'images/', 'portal/', 'index/', '')

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.base_url + end) for end in EXPECTED_URLS)
        )

    def test_no_index(self):
        raise SkipTest('FIXME: The index/ in EXPECTED_URLS is a bug!')

    def test_recursive(self):
        self._scan(
            self._run_recursive['target'], self._run_recursive['plugins'])
        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = ('spameggs/', 'test/', 'spameggs/portal/',
                         'spameggs/portal/andres/', '')

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.directory_url + end) for end in EXPECTED_URLS)
        )
