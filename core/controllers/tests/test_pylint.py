# -*- coding: utf8 -*-
'''
test_pylint.py

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
'''
import os
import sys
import unittest

from pylint import lint
from pylint.reporters.text import TextReporter
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest


class WritableObject(object):
    def __init__(self):
        self.content = []
        
    def write(self, st):
        if st == '\n':
            return
        self.content.append(st)
        
    def read(self):
        return self.content


@attr('smoke')
class PylintRunner(unittest.TestCase):

    maxDiff = None
    pylint_plugins_dir = os.path.join('core', 'controllers', 'tests',
                                      'pylint_plugins')

    def setUp(self):
        sys.path.append(self.pylint_plugins_dir)
        
    def tearDown(self):
        sys.path.remove(self.pylint_plugins_dir)
    
    def run_pylint(self, directory):
        pylint_rc = os.path.join('core', 'controllers', 'tests', 'pylint.rc')
        pylint_args = [directory, '-E', '--rcfile=%s' % pylint_rc]
        pylint_output = WritableObject()
        lint.Run(pylint_args, reporter=TextReporter(pylint_output), exit=False)
        return pylint_output
    
    def test_pylint_plugins(self):
        pylint_output = self.run_pylint('plugins/')
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_controllers(self):
        pylint_output = self.run_pylint('core/controllers/')
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_data(self):
        pylint_output = self.run_pylint('core/data/')
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_ui(self):
        raise SkipTest('Remove me after fix https://www.logilab.org/ticket/122793')
    
        pylint_output = self.run_pylint('core/ui/')
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))
