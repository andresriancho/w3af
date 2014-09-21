"""
test_basic.py

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
class TestBasicConsoleUI(ConsoleTestHelper):
    """
    Basic test for the console UI.
    """
    def test_menu_browse_misc(self):
        commands_to_run = ['misc-settings', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:misc-settings>>> ')
        assert_result, msg = self.all_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_menu_browse_http(self):
        commands_to_run = ['http-settings', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:http-settings>>> ')
        assert_result, msg = self.all_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_menu_browse_target(self):
        commands_to_run = ['target', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:target>>> ')
        assert_result, msg = self.all_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_menu_plugin_desc(self):
        commands_to_run = ['plugins',
                           'infrastructure desc zone_h',
                           'back',
                           'exit']

        expected = ('This plugin searches the zone-h.org',
                    'result. The information stored in',
                    'previous defacements to the target website.')

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_menu_set_option_case01(self):
        commands_to_run = ['target', 'set target http://moth/', 'save', 'view',
                           'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:target>>> ',
                    'The configuration has been saved.\r\n')
        assert_result, msg = self.all_expected_in_output(expected)
        self.assertTrue(assert_result, msg)
        
        expected_start_with = ('| http://moth/',)
        assert_result, msg = self.all_expected_substring_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)
        
    def test_menu_set_option_manual_save(self):
        commands_to_run = ['target set target http://moth/',
                           'target view',
                           'target save',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = ('| target ',
                               'The configuration has been saved.')
        assert_result, msg = self.startswith_expected_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)

    def test_menu_set_option_auto_save(self):
        commands_to_run = ['target set target http://moth/',
                           'target view',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = ('| target ',
                               'The configuration has been saved.')
        assert_result, msg = self.startswith_expected_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)
        
    def test_menu_set_option_invalid_case01(self):
        # Invalid port
        commands_to_run = ['target', 'set target http://moth:301801/', 'view',
                           'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected_start_with = ('Invalid URL configured by user,',
                               # Because nothing was really saved and the
                               # config is empty, this will succeed
                               'The configuration has been saved.')
        assert_result, msg = self.startswith_expected_in_output(expected_start_with)
        self.assertTrue(assert_result, msg)

