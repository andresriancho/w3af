# -*- encoding: utf-8 -*-
"""
test_is_source_file.py

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

from w3af.core.controllers.misc.is_source_file import is_source_file


class TestIsSourceFile(unittest.TestCase):
    
    def test_php(self):
        source = 'foo <? echo "a"; ?> bar'
        match, lang = is_source_file(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, 'PHP')
    
    def test_no_code_case01(self):
        source = 'foo <? echo "bar'
        match, lang = is_source_file(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)
    
    def test_no_code_case02(self):
        source = 'foo <?xml ?> "bar'
        match, lang = is_source_file(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)

    def test_no_code_case03(self):
        source = 'foo <?xpacket ?> "bar'
        match, lang = is_source_file(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)

    def test_no_code_case04(self):
        source = 'foo <?ypacket ?> "bar'
        match, lang = is_source_file(source)
        
        self.assertNotEqual(match, None)
        self.assertEqual(lang, 'PHP')
