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
from core.data.profile.profile import profile


@attr('smoke')
class TestProfilesConsoleUI(ConsoleTestHelper):
    '''
    Load profiles from the console UI.
    '''
    def setUp(self):
        super(TestProfilesConsoleUI, self).setUp()
        self._remove_if_exists('unittest')
    
    def tearDown(self):
        super(TestProfilesConsoleUI, self).tearDown()
        self._remove_if_exists('unittest')
    
    def _remove_if_exists(self, profile_name):
        try:
            profile_inst = profile(profile_name)
            profile_inst.remove()
        except:
            pass
    
    def _assert_exists(self, profile_name):
        try:
            profile(profile_name)
        except:
            assert False, 'The %s profile does NOT exist!' % profile_name
        
    def test_load_profile_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use OWASP_TOP10',
                           'exit']

        expected = (
            'The plugins configured by the scan profile have been enabled',
            'Please set the target URL',
            ' | Use a profile.')

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.all_expected_substring_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_load_profile_not_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use do_not_exist',
                           'exit']

        expected = ('Unknown profile name: "do_not_exist"',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

    def test_save_as_profile(self):
        commands_to_run = ['profiles',
                           'use OWASP_TOP10',
                           'save_as unittest',
                           'exit']

        expected = ('Profile saved.',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)
        
        self._assert_exists('unittest')

    def test_save_load_misc_settings(self):
        # Save the settings
        commands_to_run = ['misc-settings set msf_location /etc/',
                           'profiles save_as unittest',
                           'exit']

        expected = ('Profile saved.',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)
        
        self._assert_exists('unittest')
        
        # Clean the mocked stdout
        self._mock_stdout.clear()
        
        # Load the settings
        commands_to_run = ['profiles',
                           'use unittest',
                           'back',
                           'misc-settings view',
                           'exit']

        expected = ('/etc/',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.all_expected_substring_in_output(expected)
        self.assertTrue(assert_result, msg)
