"""
test_bruteforcer.py

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
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.bruteforce.bruteforcer import (PasswordBruteforcer,
                                                          UserPasswordBruteforcer)


class TestPasswordBruteforcer(unittest.TestCase):

    @attr('smoke')
    def test_contains(self):
        url = URL('http://www.w3af.org/')

        pwd_bf = PasswordBruteforcer(url)

        self.assertTrue('password' in pwd_bf.generator())
        self.assertTrue('123456' in pwd_bf.generator())
        self.assertTrue('12345' in pwd_bf.generator())


class TestUserPasswordBruteforcer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = create_temp_dir()

    @attr('smoke')
    def test_bruteforcer_default(self):
        url = URL('http://www.w3af.org/')

        bf = UserPasswordBruteforcer(url)

        expected_combinations = [
            ('prueba1', '123abc'),
            ('test', 'freedom'),
            ('user', 'letmein'),
            ('www.w3af.org', 'master'),    # URL feature
            ('admin', '7emp7emp'),         # l337 feature
            ('user1', ''),                 # No password
            ('user1',
             'user1')             # User eq password
        ]
        generated = []

        for (user, pwd) in bf.generator():
            generated.append((user, pwd))

        for expected_comb in expected_combinations:
            self.assertTrue(expected_comb in generated)

    @attr('smoke')
    def test_bruteforcer_combo(self):

        expected_combinations = [
            ('test', 'unittest'),
            ('123', 'unittest'),
            ('unittest', 'w00tw00t!'),
            ('unittest', 'unittest')
        ]

        combo_filename = os.path.join(self.temp_dir, 'combo.txt')
        combo_fd = file(combo_filename, 'w')

        for user, password in expected_combinations:
            combo_fd.write('%s:%s\n' % (user, password))

        combo_fd.close()

        url = URL('http://www.w3af.org/')

        bf = UserPasswordBruteforcer(url)
        bf.combo_file = combo_filename
        bf.combo_separator = ':'

        generated = []

        for (user, pwd) in bf.generator():
            generated.append((user, pwd))

        for expected_comb in expected_combinations:
            self.assertTrue(expected_comb in generated)
