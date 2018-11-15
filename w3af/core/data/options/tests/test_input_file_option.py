"""
test_input_file_option.py

Copyright 2015 Andres Riancho

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
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.input_file_option import InputFileOption
from w3af.core.controllers.misc.temp_dir import (create_temp_dir,
                                                 remove_temp_dir)


class TestInputFileOption(unittest.TestCase):

    INPUT_FILE = os.path.relpath(os.path.join(ROOT_PATH, 'core', 'data',
                                              'options', 'tests', 'test.txt'))

    def setUp(self):
        create_temp_dir()

    def tearDown(self):
        remove_temp_dir()

    def test_valid_base64_data(self):
        value = '%s%s' % (InputFileOption.DATA_PROTO,
                          'xyz'.encode('zlib').encode('base64').strip())
        opt = opt_factory('name', value, 'desc', INPUT_FILE, 'help', 'tab')

        self.assertEqual(opt.get_value_for_profile(), value)
        self.assertEqual(file(opt.get_value()).read(), 'xyz')

        self.assertEqual(opt.get_default_value(), opt.get_value())

        self.assertIn('/tmp/', opt.get_value())
        self.assertIn(InputFileOption.DATA_PREFIX, opt.get_value())
        self.assertIn(InputFileOption.DATA_SUFFIX, opt.get_value())

        # Cleanup
        os.unlink(opt.get_value())

    def test_invalid_base64_data(self):
        value = '%s%s' % (InputFileOption.DATA_PROTO, 'x')
        self.assertRaises(BaseFrameworkException, opt_factory, 'name', value,
                          'desc', INPUT_FILE, 'help', 'tab')

    def test_save_file_as_self_contained(self):
        opt = opt_factory('name', self.INPUT_FILE, 'desc',
                          INPUT_FILE, 'help', 'tab')

        self.assertIn(InputFileOption.DATA_PROTO,
                      opt.get_value_for_profile(self_contained=True))

    def test_relative_path(self):
        opt = opt_factory('name', self.INPUT_FILE, 'desc',
                          INPUT_FILE, 'help', 'tab')

        self.assertEquals(opt.get_value(), self.INPUT_FILE)

    def test_relative_path_full_path_input(self):
        full_path = os.path.join(ROOT_PATH, 'core', 'data',
                                 'options', 'tests', 'test.txt')

        relative_path = os.path.relpath(full_path)

        opt = opt_factory('name', full_path, 'desc',
                          INPUT_FILE, 'help', 'tab')

        self.assertEquals(opt.get_value(), relative_path)

    def test_relative_path_when_cwd_is_root(self):
        # Change the CWD to root
        old_cwd = os.getcwd()
        os.chdir('/')

        full_path = os.path.join(ROOT_PATH, 'core', 'data',
                                 'options', 'tests', 'test.txt')

        relative_path = os.path.relpath(full_path)

        opt = opt_factory('name', full_path, 'desc',
                          INPUT_FILE, 'help', 'tab')

        self.assertEquals(opt.get_value(), relative_path)

        # Restore the previous CWD
        os.chdir(old_cwd)
