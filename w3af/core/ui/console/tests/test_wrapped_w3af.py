"""
test_wrapped_w3af.py

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
import unittest
import subprocess
import sys
import datetime

from w3af.core.data.db.startup_cfg import StartUpConfig


class TestWrappedW3afConsole(unittest.TestCase):
    def test_wrapped_w3af(self):
        """
        Strange behaviour when wrapping w3af_console
        https://github.com/andresriancho/w3af/issues/1299
        """
        # Just in case... we don't want to break other tests
        startup_cfg = StartUpConfig()
        startup_cfg.last_upd = datetime.date.today()
        startup_cfg.set_accepted_disclaimer(True)
        startup_cfg.save()

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
                           'back',
                           'misc-settings',
                           'view',
                           'back',
                           'exit']

        expected_output = 'msf_location'

        stdout, stderr = p.communicate('\r'.join(commands_to_run) + '\r')

        msg = 'Failed to find "%s" in "%s" using "%s" as python executable.'
        msg = msg % (expected_output, stdout, python_executable)
        self.assertIn(expected_output, stdout, msg)
