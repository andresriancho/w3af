'''
test_w3af_console.py

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
import unittest
import compiler
import subprocess
import fcntl
import os
import time

from nose.plugins.attrib import attr
from w3af.core.controllers.misc.which import which
from w3af.core.data.db.startup_cfg import StartUpConfig


def non_block_read(output):
    '''
    Note: Only supports unix platform!
        http://docs.python.org/2/library/fcntl.html
        Platforms: Unix
    '''
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""


class TestW3afConsole(unittest.TestCase):
    @attr('ci_fails')
    def test_compiles(self):
        try:
            compiler.compile(
                file('w3af_console').read(), '/tmp/foo.tmp', 'exec')
        except SyntaxError, se:
            self.assertTrue(False, 'Error in w3af_console code "%s"' % se)

    @attr('ci_fails')
    def test_get_prompt(self):
        # We want to get the prompt, not a disclaimer message
        startup_cfg = StartUpConfig()
        startup_cfg.accepted_disclaimer = True
        startup_cfg.save()

        # The easy way to do this was to simply pass 'python' to Popen
        # but now that we want to run the tests in virtualenv, we need to
        # find the "correct" / "virtual" python executable using which and
        # then pass that one to Popen
        python_executable = which('python')[0]
        
        p = subprocess.Popen([python_executable, 'w3af_console', '-n'],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        
        # Wait for the subprocess to start and the prompt to appear
        time.sleep(15)
        
        expected_prompt = 'w3af>>>'
        prompt = non_block_read(p.stdout)
        
        msg = 'Failed to find "%s" in "%s" using "%s" as python executable.'
        msg = msg % (expected_prompt, prompt, python_executable)
        self.assertTrue(prompt.startswith(expected_prompt), msg)
        
        p.kill()