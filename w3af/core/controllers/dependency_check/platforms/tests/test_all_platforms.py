"""
test_all_platforms.py

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

from ..current_platform import KNOWN_PLATFORMS
from ..base_platform import CORE, GUI


class TestAllPlatforms(unittest.TestCase):
    def test_os_detection(self):
        # I really need those platform detection functions to be specific!
        results = [p.is_current_platform() for p in KNOWN_PLATFORMS]
        self.assertEqual(1, results.count(True), results)

    def test_attributes(self):
        REQUIRED_ATTRS = ['PIP_PACKAGES', 'SYSTEM_PACKAGES', 'SYSTEM_NAME',
                          'PKG_MANAGER_CMD', 'PIP_CMD']

        for required_attr in REQUIRED_ATTRS:
            for platform in KNOWN_PLATFORMS:
                self.assertTrue(hasattr(platform, required_attr))

    def test_core_and_gui_deps(self):
        for platform in KNOWN_PLATFORMS:
            for dependency_set in {CORE, GUI}:
                self.assertIn(dependency_set, platform.PIP_PACKAGES)
                self.assertIn(dependency_set, platform.SYSTEM_PACKAGES)

    def test_gui_includes_core(self):
        for platform in KNOWN_PLATFORMS:
            self.assertTrue(set(platform.PIP_PACKAGES[CORE]).issubset(platform.PIP_PACKAGES[GUI]))
            self.assertTrue(set(platform.SYSTEM_PACKAGES[CORE]).issubset(platform.SYSTEM_PACKAGES[GUI]))

    def test_more_than_three_dependencies(self):
        for platform in KNOWN_PLATFORMS:
            for dependency_set in {CORE, GUI}:
                self.assertGreater(len(platform.PIP_PACKAGES[dependency_set]), 3)

    def test_os_package_is_installed(self):
        # Just looking for exceptions
        [p.os_package_is_installed('foo') for p in KNOWN_PLATFORMS]

    def test_after_hook(self):
        # Just looking for exceptions
        [p.after_hook() for p in KNOWN_PLATFORMS]