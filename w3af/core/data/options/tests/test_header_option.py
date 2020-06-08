"""
test_header_option.py

Copyright 2018 Andres Riancho

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

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import HEADER


class TestQueryStringOption(unittest.TestCase):

    def test_valid_header(self):
        value = 'Basic: bearer 0x12345\r\n'
        opt = opt_factory('name', value, 'desc', HEADER, 'help', 'tab')

        self.assertEqual(opt.get_value_for_profile(), value)

        header_instance = opt.get_value()

        self.assertIn('Basic', header_instance)
        self.assertEqual(header_instance['Basic'], 'bearer 0x12345')

    def test_empty_header(self):
        value = ''
        opt = opt_factory('name', value, 'desc', HEADER, 'help', 'tab')

        self.assertEqual(opt.get_value_for_profile(), value)

        header_instance = opt.get_value()
        self.assertEqual(len(header_instance), 0)
