# -*- coding: utf8 -*-
"""
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
"""
import os
import unittest

from pylint import lint
from pylint.reporters.text import TextReporter
from nose.plugins.attrib import attr

from w3af import ROOT_PATH


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
    
    def run_pylint(self, directory):
        pylint_rc = os.path.join(ROOT_PATH, 'core', 'controllers', 'tests',
                                 'pylint.rc')
        pylint_args = [directory, '-E', '--rcfile=%s' % pylint_rc]
        pylint_output = WritableObject()
        lint.Run(pylint_args, reporter=TextReporter(pylint_output), exit=False)
        return pylint_output
    
    def test_pylint_plugins(self):
        pylint_output = self.run_pylint('%s/plugins/' % ROOT_PATH)
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_controllers(self):
        pylint_output = self.run_pylint('%s/core/controllers/' % ROOT_PATH)
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_data(self):
        pylint_output = self.run_pylint('%s/core/data/' % ROOT_PATH)
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))

    def test_pylint_core_ui(self):
        pylint_output = self.run_pylint('%s/core/ui/' % ROOT_PATH)
        output = pylint_output.read()
        self.assertEqual(output, [], '\n'.join(output))
