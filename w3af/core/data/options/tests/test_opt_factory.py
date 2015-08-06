"""
test_opt_factory.py

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
import os
import unittest

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.doc.url import URL as URL_KLASS
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import (
    BOOL, INT, POSITIVE_INT, FLOAT, STRING, IPPORT, LIST,
    REGEX, COMBO, INPUT_FILE, OUTPUT_FILE,
    PORT, IP, URL, URL_LIST)


class TestOptionFactory(unittest.TestCase):

    SHORT_INPUT_FILE = '%ROOT_PATH%/core/data/options/tests/test.txt'
    INPUT_FILE = os.path.relpath(os.path.join(ROOT_PATH, 'core', 'data',
                                              'options', 'tests', 'test.txt'))

    def test_factory_ok(self):
        input_file = self.INPUT_FILE
        output_file = self.INPUT_FILE

        data = {BOOL: [('true', True)],
                INT: [('1', 1)],
                POSITIVE_INT: [('2', 2)],
                FLOAT: [('1.0', 1.0)],
                STRING: [('hello world', 'hello world')],
                URL: [('http://moth/', URL_KLASS('http://moth/'))],
                URL_LIST: [('http://moth/1 , http://moth/2',
                           [URL_KLASS('http://moth/1'),
                            URL_KLASS('http://moth/2')])],
                IPPORT: [('127.0.0.1:8080', '127.0.0.1:8080')],
                LIST: [('a,b,c', ['a', 'b', 'c'])],
                REGEX: [('.*', '.*')],
                COMBO: [(['a', 'b', 'c'], 'a')],
                INPUT_FILE: [(input_file, input_file)],
                OUTPUT_FILE: [(output_file, output_file)],
                PORT: [('12345', 12345)],
                IP: [('127.0.0.1', '127.0.0.1'),
                     (None, None)]
                }

        for _type in data:
            for user_value, parsed_value in data[_type]:
                opt = opt_factory('name', user_value, 'desc', _type,
                                  'help', 'tab1')
    
                self.assertEqual(opt.get_name(), 'name')
                self.assertEqual(opt.get_desc(), 'desc')
                self.assertEqual(opt.get_type(), _type)
                self.assertEqual(opt.get_default_value(), parsed_value)
                self.assertEqual(opt.get_value(), parsed_value)
                self.assertEqual(opt.get_help(), 'help')
                self.assertEqual(opt.get_tabid(), 'tab1')
    
                self.assertIsInstance(opt.get_name(), basestring)
                self.assertIsInstance(opt.get_desc(), basestring)
                self.assertIsInstance(opt.get_type(), basestring)
                self.assertIsInstance(opt.get_help(), basestring)

    def test_factory_unknown_type(self):
        self.assertRaises(KeyError, opt_factory, 'name', 'value', 'desc',
                          'unknown_type')

    def test_invalid_data(self):
        input_file = os.path.join(ROOT_PATH, 'core', 'data', 'foobar',
                                  'does-not-exist.txt')
        output_file = input_file

        data = {BOOL: ['rucula'],
                INT: ['0x32'],
                POSITIVE_INT: ['-1'],
                FLOAT: ['1x2'],
                URL: ['http://', '/', ''],
                URL_LIST: ['http://moth/1 , http://moth:333333'],
                IPPORT: ['127.0.0.1'],
                IP: ['127.0.0.', '127.0.0', '3847398740'],
                REGEX: ['.*('],
                INPUT_FILE: [input_file, '/', 'base64://'],
                OUTPUT_FILE: [output_file, '/'],
                PORT: ['65536']
                }

        for _type in data:
            for fake_value in data[_type]:
                err = '%s for an option of type %s should raise an exception.'
                try:
                    opt_factory('name', fake_value, 'desc', _type)
                except BaseFrameworkException:
                    self.assertTrue(True)
                else:
                    self.assertTrue(False, err % (fake_value, _type))

    def test_factory_already_converted_type(self):
        data = {BOOL: (True, True),
                INT: (1, 1),
                FLOAT: (1.0, 1.0),
                STRING: ('hello world', 'hello world'),
                URL: (URL_KLASS('http://moth/'), URL_KLASS('http://moth/')),
                URL_LIST: ([URL_KLASS('http://moth/1'),
                            URL_KLASS('http://moth/2')],
                           [URL_KLASS('http://moth/1'),
                            URL_KLASS('http://moth/2')]),
                LIST: (['a', 'b', 'c'], ['a', 'b', 'c']),
                PORT: (12345, 12345)
                }

        for _type, (user_value, parsed_value) in data.iteritems():
            opt = opt_factory('name', user_value, 'desc', _type)

            self.assertEqual(opt.get_name(), 'name')
            self.assertEqual(opt.get_desc(), 'desc')
            self.assertEqual(opt.get_type(), _type)
            self.assertEqual(opt.get_default_value(), parsed_value)
            self.assertEqual(opt.get_value(), parsed_value)

            self.assertIsInstance(opt.get_name(), basestring)
            self.assertIsInstance(opt.get_desc(), basestring)
            self.assertIsInstance(opt.get_type(), basestring)
            self.assertIsInstance(opt.get_help(), basestring)

    def test_root_path_variable_get(self):
        opt = opt_factory('name', self.INPUT_FILE, 'desc', INPUT_FILE,
                          'help', 'tab1')

        self.assertEqual(opt.get_value_for_profile(), self.SHORT_INPUT_FILE)
        self.assertEqual(opt.get_value_str(), self.INPUT_FILE)

    def test_root_path_variable_init(self):
        opt = opt_factory('name', self.SHORT_INPUT_FILE, 'desc', INPUT_FILE,
                          'help', 'tab1')

        self.assertEqual(opt.get_value_for_profile(), self.SHORT_INPUT_FILE)
        self.assertEqual(opt.get_value_str(), self.INPUT_FILE)
        self.assertEqual(opt._value, self.INPUT_FILE)

    def test_root_path_variable_set(self):
        opt = opt_factory('name', self.SHORT_INPUT_FILE, 'desc', INPUT_FILE,
                          'help', 'tab1')

        opt.set_value(self.SHORT_INPUT_FILE)

        self.assertEqual(opt.get_value_for_profile(), self.SHORT_INPUT_FILE)
        self.assertEqual(opt.get_value_str(), self.INPUT_FILE)
        self.assertEqual(opt._value, self.INPUT_FILE)
