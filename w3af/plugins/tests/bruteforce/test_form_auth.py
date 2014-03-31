"""
test_form_auth.py

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


class TestFormAuth(PluginTest):
    
    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'bruteforce')
    
    small_users_negative = os.path.join(BASE_PATH, 'small-users-negative.txt')
    small_users_positive = os.path.join(BASE_PATH, 'small-users-positive.txt')
    small_passwords = os.path.join(BASE_PATH, 'small-passwords.txt')

    target_post_url = get_moth_http('/bruteforce/form/guessable_login_form.py')
    target_get_url = get_moth_http('/bruteforce/form/guessable_login_form_get.py')
    target_password_only_url = get_moth_http('/bruteforce/form/guessable_pass_only.py')
    target_negative_url = get_moth_http('/bruteforce/form/impossible.py')

    target_web_spider_url = get_moth_http('/bruteforce/form/')

    positive_test = {
        'target': None,
        'plugins': {
            'bruteforce': (PluginConfig('form_auth',
                                        ('usersFile', small_users_positive,
                                         PluginConfig.STR),
                                        ('passwdFile', small_passwords,
                                         PluginConfig.INPUT_FILE),
                                        ('useProfiling', False,
                                         PluginConfig.BOOL),
                                        ),
                           ),
        }
    }

    negative_test = {
        'target': None,
        'plugins': {
            'bruteforce': (PluginConfig('form_auth',
                                        ('usersFile', small_users_negative,
                                         PluginConfig.STR),
                                        (
                                        'passwdFile', small_passwords,
                                        PluginConfig.INPUT_FILE),
                                        ('useProfiling', False,
                                         PluginConfig.BOOL),
                                        ),
                           )
        }
    }

    @attr('smoke')
    def test_found_credentials_post(self):
        self._scan(self.target_post_url, self.positive_test['plugins'])

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string, self.target_post_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], '1234')

    def test_found_credentials_get(self):
        self._scan(self.target_get_url, self.positive_test['plugins'])

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string, self.target_get_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], 'admin')

    def test_found_credentials_password_only(self):
        self._scan(self.target_password_only_url,
                   self.positive_test['plugins'])

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string,
                          self.target_password_only_url)
        self.assertEquals(vuln['user'], 'password-only-form')
        self.assertEquals(vuln['pass'], '1234')

    def test_negative(self):
        self._scan(self.target_negative_url, self.negative_test['plugins'])

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 0)
