"""
test_shell_handler.py

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

import w3af.core.data.kb.knowledge_base as kb

from w3af.plugins.attack.payloads.shell_handler import (get_webshells,
                                                        get_shell_code)


class TestShellHandler(unittest.TestCase):

    TEST_CMD = 'ls'

    def test_get_shell_code_extension(self):
        shells = get_shell_code('php', self.TEST_CMD)
        
        self.assertEqual(len(shells), 2)
        php_shell_code, lang, shellcode_generator = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)

    def test_get_shell_code_extension_force(self):
        shells = get_shell_code('php', self.TEST_CMD, True)
        
        self.assertEqual(len(shells), 1)
        php_shell_code, lang, shellcode_generator = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)

    def test_get_shell_code_no_extension(self):
        shells = get_shell_code('', self.TEST_CMD)
        
        self.assertEqual(len(shells), 2)
        php_shell_code, lang, shellcode_generator = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)

    def test_get_shell_code_invalid_extension(self):
        shells = get_shell_code('123456', self.TEST_CMD)
        
        self.assertEqual(len(shells), 2)
        php_shell_code, lang, shellcode_generator = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)
        
    def test_get_web_shell_extension(self):
        shells = get_webshells('php')
        
        self.assertEqual(len(shells), 6)
        # The first one is PHP since we asked for it when we passed PHP as
        # parameter
        php_shell_code, lang = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)

    def test_get_web_shell_code_extension_force(self):
        shells = get_webshells('php', True)

        # Only one returned since we're forcing the extension        
        self.assertEqual(len(shells), 1)
        php_shell_code, lang = shells[0]
        
        self.assertEqual(lang, 'php')
        self.assertIn('echo ', php_shell_code)

    def test_get_web_shell_code_no_extension(self):
        shells = get_webshells('')
        
        # All returned when invalid extension
        self.assertEqual(len(shells), 6)

    def test_get_web_shell_code_invalid_extension(self):
        shells = get_webshells('123456')
        
        # All returned when invalid extension
        self.assertEqual(len(shells), 6)
    
    def test_with_kb_data(self):
        kb.kb.raw_write('server_header', 'powered_by_string', ['ASP foo bar',])
        
        shells = get_webshells('')
        
        # TODO: The shells list has duplicates, fix in the future. Not really a
        #       big issue since it would translate into 1 more HTTP request and
        #       only in the cases where the user is exploiting something
        self.assertEqual(len(shells), 7)
        
        # The first one is ASP since we're scanning (according to the KB) an
        # ASP site
        asp_shell_code, lang = shells[0]
        
        self.assertEqual(lang, 'asp')
        self.assertIn('WSCRIPT.SHELL', asp_shell_code)
        
        kb.kb.cleanup()