# -*- coding: utf8 -*-
'''
test_pylint.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
import unittest

from pylint import lint
from pylint.reporters.text import TextReporter


class WritableObject(object):
    def __init__(self):
        self.content = []
        
    def write(self, st):
        self.content.append(st)
        
    def read(self):
        return self.content

class PylintRunner(unittest.TestCase):

    maxDiff = None
    
    def run_pylint(self, directory):
        pylint_args = [directory, "-E",]
        pylint_output = WritableObject()
        lint.Run(pylint_args, reporter=TextReporter(pylint_output), exit=False)
        return pylint_output
    
    def test_pylint_plugins(self):
        pylint_output = self.run_pylint('plugins/')
        self.assertEqual(pylint_output.read(), [])

    def test_pylint_core_controllers(self):
        pylint_output = self.run_pylint('core/controllers/')
        self.assertEqual(pylint_output.read(), [])

    def test_pylint_core_data(self):
        pylint_output = self.run_pylint('core/data/')
        self.assertEqual(pylint_output.read(), [])

    def test_pylint_core_ui(self):
        pylint_output = self.run_pylint('core/ui/')
        self.assertEqual(pylint_output.read(), [])
