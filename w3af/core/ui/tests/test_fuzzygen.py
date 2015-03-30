"""
test_fuzzygen.py

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

from w3af.core.ui.gui.tools.helpers.fuzzygen import FuzzyGenerator, FuzzyError


class TestAll(unittest.TestCase):
    def test_simple_doubledollar(self):
        fg = FuzzyGenerator("Hola \$mundo\ncruel", "")
        self.assertEqual(fg.sane1, ["Hola $mundo\ncruel"])

        fg = FuzzyGenerator("Hola \$mundo\ncruel\$", "")
        self.assertEqual(fg.sane1, ["Hola $mundo\ncruel$"])

        fg = FuzzyGenerator("Hola \$mundo\ncruel\$asdfg\$\$gh", "")
        self.assertEqual(fg.sane1, ["Hola $mundo\ncruel$asdfg$$gh"])

    def test_quantities(self):
        fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
        self.assertEqual(fg.calculate_quantity(), 4)

        fg = FuzzyGenerator("$range(2)$ n$'as'$", "p$string.lowercase[:2]$")
        self.assertEqual(fg.calculate_quantity(), 8)

    def test_generations(self):
        fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
        self.assertEqual(list(fg.generate()), [
            ('0 dnda', 'pp'), ('0 dnds', 'pp'),
            ('1 dnda', 'pp'), ('1 dnds', 'pp')])

        fg = FuzzyGenerator("$range(2)$ d$'as'$", "p$string.lowercase[:2]$")
        self.assertEqual(list(fg.generate()), [
            ('0 da', 'pa'), ('0 da', 'pb'), ('0 ds', 'pa'), ('0 ds', 'pb'),
            ('1 da', 'pa'), ('1 da', 'pb'), ('1 ds', 'pa'), ('1 ds', 'pb'),
        ])

    def test_quant_gen_gen(self):
        fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
        self.assertEqual(fg.calculate_quantity(), 4)

        self.assertEqual(list(fg.generate()), [
            ('0 dnda', 'pp'), ('0 dnds', 'pp'),
            ('1 dnda', 'pp'), ('1 dnds', 'pp')])

    def test_noniterable(self):
        self.assertRaises(FuzzyError, FuzzyGenerator, "", "aa $3$ bb")
        self.assertRaises(FuzzyError, FuzzyGenerator, "",
                          "aa $[].extend([1,2])$ bb")

    def test_inside_doubledollar(self):
        fg = FuzzyGenerator(
            "GET http://localhost/$['aaa\$b', 'b\$ccc']$ HTTP/1.0", "")
        self.assertEqual(list(fg.generate()), [
            ("GET http://localhost/aaa$b HTTP/1.0", ""),
            ("GET http://localhost/b$ccc HTTP/1.0", ""),
        ])

    def test_double_token_together(self):
        # from bug 2393362, the idea is to generate 00 to 99
        # using to generators (I'm doing less iterations here)
        fg = FuzzyGenerator("-$xrange(2)$$xrange(2)$-", "")
        self.assertEqual(list(fg.generate()), [
            ("-00-", ""), ("-01-", ""), ("-10-", ""), ("-11-", "")])

