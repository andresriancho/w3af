'''
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
'''
from nose.plugins.attrib import attr

from core.ui.console.console_ui import ConsoleUI
from core.ui.console.tests.helper import ConsoleTestHelper


@attr('smoke')
class TestBasicConsoleUI(ConsoleTestHelper):
    '''
    Basic test for the console UI.
    '''
    def test_menu_browse_misc(self):
        commands_to_run = ['misc-settings', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:misc-settings>>> ')
        self.assertTrue(self.all_expected_in_output(expected),
                        self._mock_stdout.messages)

    def test_menu_browse_http(self):
        commands_to_run = ['http-settings', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:http-settings>>> ')
        self.assertTrue(self.all_expected_in_output(expected),
                        self._mock_stdout.messages)

    def test_menu_browse_target(self):
        commands_to_run = ['target', 'back', 'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('w3af>>> ', 'w3af/config:target>>> ')
        self.assertTrue(self.all_expected_in_output(expected),
                        self._mock_stdout.messages)

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

        self.assertTrue(self.startswith_expected_in_output(expected),
                        self._mock_stdout.messages)
