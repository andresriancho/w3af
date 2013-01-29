'''
test_profiles.py

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
class TestProfilesConsoleUI(ConsoleTestHelper):
    '''
    Load profiles from the console UI.
    '''

    def test_load_profile_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use OWASP_TOP10',
                           'exit']

        expected = (
            'The plugins configured by the scan profile have been enabled',
            'Please set the target URL',
            '| use                            | Use a profile.')

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        self.assertTrue(self.startswith_expected_in_output(expected),
                        self._mock_stdout.messages)

    def test_load_profile_not_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use do_not_exist',
                           'exit']

        expected = ('Unknown profile name: "do_not_exist"',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        self.assertTrue(self.startswith_expected_in_output(expected),
                        self._mock_stdout.messages)
