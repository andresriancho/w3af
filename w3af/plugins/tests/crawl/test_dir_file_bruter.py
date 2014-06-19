"""
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
"""
import os

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http


class TestDirFileBruter(PluginTest):

    TEST_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                             'dir_file_bruter')

    DIR_DB_PATH = os.path.join(TEST_PATH, 'test_dirs_small.db')
    FILE_DB_PATH = os.path.join(TEST_PATH, 'test_files_small.db')

    directory_url = get_moth_http('/crawl/dir_bruter/')
    base_url = get_moth_http()

    _run_directories = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('dir_file_bruter',
                                           ('dir_wordlist',
                                            DIR_DB_PATH,
                                            PluginConfig.INPUT_FILE),),)}
    }

    _run_files = {
        'target': base_url,
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
        self._scan(self._run_directories['target'],
                   self._run_directories['plugins'])

        expected_urls = ('/crawl/', '/portal/', '/')
        self.assertAllURLsFound(expected_urls)

    def test_files(self):
        self._scan(self._run_files['target'], self._run_files['plugins'])

        expected_urls = ('/iamhidden.txt', '/')
        self.assertAllURLsFound(expected_urls)
    
    def test_directories_files(self):
        self._scan(self._run_directory_files['target'],
                   self._run_directory_files['plugins'])

        expected_urls = (u'/crawl/dir_bruter/',
                         u'/crawl/dir_bruter/hidden-inside-dir.txt',
                         u'/crawl/dir_bruter/spameggs/')
        self.assertAllURLsFound(expected_urls)

    def test_recursive(self):
        self._scan(self._run_recursive['target'],
                   self._run_recursive['plugins'])

        expected_urls = (u'/crawl/dir_bruter/',
                         u'/crawl/dir_bruter/spameggs/foobar/',
                         u'/crawl/dir_bruter/spameggs/')
        self.assertAllURLsFound(expected_urls)
