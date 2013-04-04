'''
test_dir_file_bruter.py

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

from plugins.tests.helper import PluginTest, PluginConfig
from nose.plugins.skip import SkipTest


class TestDirFileBruter(PluginTest):

    TEST_PATH = os.path.join('plugins', 'tests', 'crawl', 'dir_file_bruter')

    DIR_DB_PATH = os.path.join(TEST_PATH, 'test_dirs_small.db')
    FILE_DB_PATH = os.path.join(TEST_PATH, 'test_files_small.db')

    directory_url = 'http://moth/w3af/crawl/dir_file_bruter/'
    base_url = 'http://moth/'

    _run_directories = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('dir_file_bruter',
                                           ('dir_wordlist',
                                            DIR_DB_PATH,
                                            PluginConfig.INPUT_FILE),
                                           ),)}
    }

    _run_files = {
        'target': directory_url,
        'plugins': {'crawl': (PluginConfig('dir_file_bruter',
                                           ('file_wordlist',
                                            FILE_DB_PATH,
                                            PluginConfig.INPUT_FILE),
                                           ('bf_files',
                                            True,
                                            PluginConfig.BOOL),
                                           ('bf_directories',
                                            False,
                                            PluginConfig.BOOL),
                                           ),)}
    }

    _run_directory_files = {
        'target': directory_url,
        'plugins': {'crawl': (PluginConfig('dir_file_bruter',
                                           
                                           ('dir_wordlist',
                                            DIR_DB_PATH,
                                            PluginConfig.INPUT_FILE),
                                           ('bf_directories',
                                            True,
                                            PluginConfig.BOOL),
                                           
                                           ('file_wordlist',
                                            FILE_DB_PATH,
                                            PluginConfig.INPUT_FILE),
                                           ('bf_files',
                                            True,
                                            PluginConfig.BOOL),
                                           ),)}
    }
    
    _run_recursive = {
        'target': directory_url,
        'plugins': {'crawl': (PluginConfig('dir_file_bruter',
                                           
                                           ('dir_wordlist',
                                            DIR_DB_PATH,
                                            PluginConfig.INPUT_FILE),
                                           ('bf_directories',
                                            True,
                                            PluginConfig.BOOL),
                                           
                                           ('be_recursive',
                                            True,
                                            PluginConfig.BOOL)
                                           ),)}
    }

    def test_directories(self):
        self._scan(self._run_directories['target'], self._run_directories['plugins'])
        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = (
            'setup/', 'header/', 'images/', 'portal/', 'index/', '')

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.base_url + end) for end in EXPECTED_URLS)
        )

    def test_files(self):
        self._scan(self._run_files['target'], self._run_files['plugins'])
        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = (
            'iamhidden.txt', '')

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.directory_url + end) for end in EXPECTED_URLS)
        )
    
    def test_directories_files(self):
        self._scan(self._run_directory_files['target'], self._run_directory_files['plugins'])
        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = (
            'iamhidden.txt', 'spameggs/', 'test/', '')

        self.assertEquals(
            set(str(u) for u in urls),
            set((self.directory_url + end) for end in EXPECTED_URLS)
        )
    
    def test_no_index(self):
        '''
        :see: test_directories , EXPECTED_URLS
        '''
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
