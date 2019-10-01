"""
test_basic_auth.py

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
from w3af.core.controllers.ci.moth import get_moth_http


class TestBasicAuth(PluginTest):

    target_url_easy = get_moth_http('/auth/basic/weak/')
    target_url_impossible = get_moth_http('/auth/basic/impossible/')

    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'bruteforce')

    small_users_negative = os.path.join(BASE_PATH, 'small-users-negative.txt')
    small_users_positive = os.path.join(BASE_PATH, 'small-users-positive.txt')
    small_passwords = os.path.join(BASE_PATH, 'small-passwords.txt')

    _run_configs = {
        'positive': {
            'target': None,
            'plugins': {
                'bruteforce': (PluginConfig('basic_auth',
                                            ('users_file', small_users_positive,
                                             PluginConfig.STR),
                                            (
                                            'passwd_file', small_passwords, PluginConfig.STR),),
                               ),
                'grep': (PluginConfig('http_auth_detect'),),
            }
        },

        'negative': {
            'target': None,
            'plugins': {
                'bruteforce': (PluginConfig('basic_auth',
                                            ('users_file', small_users_negative,
                                             PluginConfig.STR),
                                            (
                                            'passwd_file', small_passwords, PluginConfig.STR),),
                               ),
                'grep': (PluginConfig('http_auth_detect'),),
            }
        }
    }

    @attr('smoke')
    def test_found_credentials(self):
        # Run the scan
        cfg = self._run_configs['positive']
        self._scan(self.target_url_easy, cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('basic_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')

        self.assertEquals(vuln.get_url().url_string, self.target_url_easy)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], 'admin')

    def test_not_found_credentials(self):
        # Run the scan
        cfg = self._run_configs['negative']
        self._scan(self.target_url_impossible, cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('basic_auth', 'auth')
        self.assertEquals(len(vulns), 0)
