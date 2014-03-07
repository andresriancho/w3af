"""
test_save.py

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
from nose.plugins.attrib import attr

from w3af.core.ui.console.console_ui import ConsoleUI
from w3af.core.ui.console.tests.helper import ConsoleTestHelper


@attr('smoke')
class TestSaveConsoleUI(ConsoleTestHelper):
    """
    Save test for the console UI.
    """
    def test_menu_simple_save(self):
        commands_to_run = ['plugins crawl config dir_file_bruter',
                           'set file_wordlist /etc/passwd',
                           'save',
                           'view',
                           'back',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = (' /etc/passwd   ',
                               'The configuration has been saved.')
        assert_result, msg = self.all_expected_substring_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)

    def test_menu_save_with_dependencies_error(self):
        commands_to_run = ['plugins audit config rfi',
                           'set use_w3af_site false',
                           'set listen_address abc',
                           'save',
                           'view',
                           'back',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = ('Identified an error with the user-defined settings',)
        assert_result, msg = self.startswith_expected_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)

    def test_menu_save_with_dependencies_success(self):
        commands_to_run = ['plugins audit config rfi',
                           'set use_w3af_site false',
                           'set listen_address 127.0.0.1',
                           'set listen_port 8081',
                           'save',
                           'view',
                           'back',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = ('127.0.0.1',
                               '8081')
        assert_result, msg = self.all_expected_substring_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)

    def test_menu_simple_save_with_view(self):
        """
        Reproduces the issue at https://github.com/andresriancho/w3af/issues/474
        where a "view" call overwrites any previously set value with the default
        """
        commands_to_run = ['plugins crawl config dir_file_bruter',
                           'set file_wordlist /etc/passwd',
                           'view',
                           'back',
                           'plugins crawl config dir_file_bruter',
                           'view',
                           'back',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = (' /etc/passwd   ',
                               'The configuration has been saved.')
        assert_result, msg = self.all_expected_substring_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)