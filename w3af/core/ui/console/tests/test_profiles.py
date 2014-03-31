"""
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
"""
import sys
import subprocess
import tempfile

from nose.plugins.attrib import attr

from w3af.core.data.db.startup_cfg import StartUpConfig
from w3af.core.ui.console.console_ui import ConsoleUI
from w3af.core.ui.console.tests.helper import ConsoleTestHelper
from w3af.core.data.profile.profile import profile


@attr('smoke')
class TestProfilesConsoleUI(ConsoleTestHelper):
    """
    Load profiles from the console UI.
    """
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

    def test_load_profile_by_filepath(self):
        tmp_profile = tempfile.NamedTemporaryFile(suffix='.pw3af')
        commands_to_run = ['profiles',
                           'help',
                           'use ' + tmp_profile.name,
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

        expected = ('The profile "do_not_exist.pw3af" wasn\'t found.',)

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

    def test_set_save_use(self):
        """
        This is a unittest for the bug reported by a user where his settings
        are not saved to the profile.

        https://github.com/andresriancho/w3af/issues/291

        Actually, the settings are saved but not properly displayed, but that's
        not so important. The important thing is that the user was seeing the
        old setting instead of the new.
        """
        # We want to get the prompt, not a disclaimer message
        startup_cfg = StartUpConfig()
        startup_cfg.accepted_disclaimer = True
        startup_cfg.save()

        # Load an existing profile, modify msf_location and save it as unittest
        commands_to_run = ['profiles',
                           'use OWASP_TOP10',
                           'back',
                           'misc-settings',
                           'set msf_location /tmp/',
                           'back',
                           'profiles',
                           'save_as unittest',
                           'exit']

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        expected = ('Profile saved.',)

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

        # The easy way to do this was to simply pass 'python' to Popen
        # but now that we want to run the tests in virtualenv, we need to
        # find the "correct" / "virtual" python executable using which and
        # then pass that one to Popen
        python_executable = sys.executable

        p = subprocess.Popen([python_executable, 'w3af_console', '-n'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             shell=False,
                             universal_newlines=True)

        # Now we run a new ConsoleUI that will load the saved settings. We
        # should see /tmp/ as the value for msf_location
        commands_to_run = ['profiles',
                           'use unittest',
                           'back',
                           'misc-settings',
                           'view',
                           'back',
                           'exit']

        expected_output = '/tmp'

        stdout, stderr = p.communicate('\r'.join(commands_to_run) + '\r')

        msg = 'Failed to find "%s" in "%s" using "%s" as python executable.'
        msg = msg % (expected_output, stdout, python_executable)
        self.assertIn(expected_output, stdout, msg)

    def test_save_as_profile_no_param(self):
        commands_to_run = ['profiles',
                           'use OWASP_TOP10',
                           'save_as',
                           'exit']

        expected = ('Parameter missing, please see the help',)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)
        
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
