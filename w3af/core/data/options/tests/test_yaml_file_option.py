"""
test_yaml_file_option.py

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
import os
import unittest

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import YAML_INPUT_FILE


class TestYamlFileOption(unittest.TestCase):

    VALID_INPUT_YAML_FILE = os.path.relpath(os.path.join(
        ROOT_PATH, 'core', 'data', 'options', 'tests', 'valid.yaml'))
    INVALID_INPUT_YAML_FILE = os.path.relpath(os.path.join(
        ROOT_PATH, 'core', 'data', 'options', 'tests', 'invalid.yaml'))

    def test_valid_yaml_file(self):
        opt = opt_factory('name', self.VALID_INPUT_YAML_FILE,
                          'desc', YAML_INPUT_FILE, 'help', 'tab')

        self.assertEqual(opt.get_value(), self.VALID_INPUT_YAML_FILE)
        self.assertEqual(opt.get_value_for_profile(),
                         '%ROOT_PATH%/core/data/options/tests/valid.yaml')

        with open(self.VALID_INPUT_YAML_FILE, 'r') as expected:
            with open(opt.get_value(), 'r') as actual:
                self.assertEqual(expected.read(), actual.read())

    def test_invalid_yaml_file(self):
        with self.assertRaises(BaseFrameworkException):
            opt_factory('name', self.INVALID_INPUT_YAML_FILE,
                        'desc', YAML_INPUT_FILE, 'help', 'tab')

    def test_file_not_exist(self):
        with self.assertRaises(BaseFrameworkException):
            opt_factory('name', 'this/does/not/exist',
                        'desc', YAML_INPUT_FILE, 'help', 'tab')
