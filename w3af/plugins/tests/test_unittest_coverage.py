"""
unittest_coverage.py

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

from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.controllers.w3afCore import w3afCore

TEST_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests')


@attr('smoke')
class TestUnittestCoverage(unittest.TestCase):

    def setUp(self):
        self.w3afcore = w3afCore()

    def test_audit(self):
        self._analyze_unittests('audit')

    def test_attack(self):
        self._analyze_unittests('attack')

    def test_output(self):
        self._analyze_unittests('output')

    def test_auth(self):
        self._analyze_unittests('auth')

    def test_crawl(self):
        self._analyze_unittests('crawl')

    def test_infrastructure(self):
        self._analyze_unittests('infrastructure')

    def test_grep(self):
        self._analyze_unittests('grep')

    def test_evasion(self):
        self._analyze_unittests('evasion')

    def test_mangle(self):
        self._analyze_unittests('mangle')

    def _analyze_unittests(self, plugin_type):
        plugins = self.w3afcore.plugins.get_plugin_list(plugin_type)

        missing = []

        for plugin in plugins:
            if not self._has_test(plugin_type, plugin):
                missing.append(plugin)

        if missing:
            msg = 'The following %s plugins dont have unittests: %s' %  \
                  (plugin_type, ', '.join(sorted(missing)))
            self.assertTrue(False, msg)

    def _has_test(self, plugin_type, plugin_name):
        tests = os.listdir(os.path.join(TEST_PATH, plugin_type))

        fname = 'test_%s.py' % plugin_name
        return fname in tests
