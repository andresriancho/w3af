"""
test_read_shell.py

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

from w3af.core.data.kb.read_shell import ReadShell
from w3af.core.data.kb.tests.test_vuln import MockVuln


class TestReadShell(unittest.TestCase):
    
    def test_help_format(self):
        shell = ReadShell(MockVuln(), None, None)
        _help = shell.help(None)
        
        self.assertFalse(_help.startswith(' '))
        
        self.assertIn('    help', _help)
        # Note that I add an extra space
        self.assertNotIn('     help', _help)
    
    def test_help_contents(self):
        shell = ReadShell(MockVuln(), None, None)
        _help = shell.help(None)
        
        self.assertNotIn('execute', _help)
        self.assertNotIn('upload', _help)
        self.assertIn('read', _help)

    def test_help_contents_specific(self):
        shell = ReadShell(MockVuln(), None, None)
        _help = shell.help('read')
        
        self.assertIn('read', _help)
        self.assertIn('/etc/passwd', _help)

