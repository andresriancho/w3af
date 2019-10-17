"""
test_string_extractor.py

Copyright 2014 Andres Riancho

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
import os

from w3af.core.data.parsers.pynarcissus.string_extractor import StringExtractor


class JSParserMixin(object):
    DATA_PATH = 'w3af/core/data/parsers/pynarcissus/tests/data/'

    def get_file_contents(self, filename):
        test_file = os.path.join(self.DATA_PATH, filename)
        return file(test_file).read()


class TestStringExtractor(unittest.TestCase, JSParserMixin):
    def test_1_js(self):
        e = StringExtractor(self.get_file_contents('test_1.js'))
        expected = {'John', 'Doe', 'blue', 'demo', ' is ', ' years old.'}

        self.assertEqual(e.get_strings(), expected)

    def test_2_js(self):
        e = StringExtractor(self.get_file_contents('test_2.js'))
        expected = {'John', 'Doe', 'blue', 'Sally', 'Rally', 'green',
                    'My father is ', '. My mother is ', 'demo'}

        self.assertEqual(e.get_strings(), expected)

    def test_3_js(self):
        e = StringExtractor(self.get_file_contents('test_3.js'))
        expected = {'Good day', 'Good evening', 'demo', ''}

        self.assertEqual(e.get_strings(), expected)
