"""
test_target.py

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
import os

from nose.plugins.attrib import attr

import w3af.core.data.kb.config as cf
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.target import CoreTarget
from w3af.core.data.parsers.doc.url import URL as URL_KLASS
from w3af.core.data.options.option_types import (BOOL, INT, FLOAT, STRING, URL,
                                                 IPPORT, LIST, REGEX, COMBO,
                                                 INPUT_FILE, OUTPUT_FILE, PORT,
                                                 URL_LIST)


OPTION_TYPES = (BOOL, INT, FLOAT, STRING, URL, IPPORT, LIST, REGEX, COMBO,
                INPUT_FILE, OUTPUT_FILE, PORT, URL_LIST)


@attr('smoke')
class TestTarget(unittest.TestCase):
    
    def test_basic(self):
        opt_lst = CoreTarget().get_options()

        for opt in opt_lst:
            self.assertIn(opt.get_type(), OPTION_TYPES)
            self.assertTrue(opt.get_name())
            self.assertEqual(opt, opt)

            # Just verify that this doesn't crash and that the types
            # are correct
            self.assertIsInstance(opt.get_name(), basestring)
            self.assertIsInstance(opt.get_desc(), basestring)
            self.assertIsInstance(opt.get_type(), basestring)
            self.assertIsInstance(opt.get_help(), basestring)
            self.assertIsInstance(opt.get_value_str(), basestring)

    def test_verify_url(self):
        ctarget = CoreTarget()

        self.assertRaises(BaseFrameworkException, ctarget._verify_url,
                          URL_KLASS('ftp://www.google.com/'))
        
        self.assertTrue(ctarget._verify_url(URL_KLASS('http://www.google.com/')))
        self.assertTrue(ctarget._verify_url(URL_KLASS('http://www.google.com:39/')))

    def test_verify_file_target(self):
        ctarget = CoreTarget()

        target_file = '/tmp/moth.target'
        target = 'file://%s' % target_file
        
        target_file_handler = file(target_file, 'w')
        target_file_handler.write('http://moth/1\n')
        target_file_handler.write('http://moth/2\n')
        target_file_handler.close()
        
        options = ctarget.get_options()
        options['target'].set_value(target)
        ctarget.set_options(options)
        
        moth1 = URL_KLASS('http://moth/1')
        moth2 = URL_KLASS('http://moth/2')
        
        self.assertIn(moth1, cf.cf.get('targets'))
        self.assertIn(moth2, cf.cf.get('targets'))
    
    def tearDown(self):
        if os.path.exists('/tmp/moth.target'):
            os.unlink('/tmp/moth.target')
