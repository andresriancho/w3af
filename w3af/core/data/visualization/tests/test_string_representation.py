"""
test_StringRepresentation.py

Copyright 2011 Andres Riancho

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

from w3af.core.data.visualization.string_representation import StringRepresentation


class TestStringRepresentation(unittest.TestCase):

    def test_one_char_40(self):
        instr = 'A\n' * 40
        si = StringRepresentation(instr, 40, 40)
        self.assertEqual(si.get_representation()[1], 25)

        self.assertEqual(si.get_representation()[0], 25)

    def test_two_chars_40(self):
        instr = 'AA\n' * 40
        si = StringRepresentation(instr, 40, 40)
        self.assertEqual(si.get_representation()[1], 10)

        self.assertEqual(si.get_representation()[0], 10)

    def test_two_chars_83(self):
        instr = 'AA\n' * 83
        si = StringRepresentation(instr, 40, 40)
        self.assertEqual(si.get_representation()[1], 20)

        self.assertEqual(si.get_representation()[0], 20)

        self.assertEqual(len(si.get_representation()), 40)

    def test_two_chars_157(self):
        instr = 'AB\n' * 157
        si = StringRepresentation(instr, 41, 40)
        self.assertEqual(len(si.get_representation()), 41)
