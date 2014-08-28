"""
test_dependency_check.py

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

from mock import patch

from ..dependency_check import dependency_check
from ..platforms.base_platform import CORE, GUI
from ..platforms.default import DefaultPlatform
from ..platforms.ubuntu1204 import Ubuntu1204
from ..pip_dependency import PIPDependency


class TestDependencyCheck(unittest.TestCase):

    DEPE_MODULE = 'w3af.core.controllers.dependency_check.dependency_check'
    CURR_PLATFORM = '%s.get_current_platform' % DEPE_MODULE
    MISSING_DEP_CMD = 'pip install rumbamanager==3.2.1'

    def setUp(self):
        self.fake_rumba_dependency = PIPDependency('rumbamanager',
                                                   'rumbamanager',
                                                   '3.2.1')

    def test_works_at_this_workstation(self):
        """
        Test that the dependency check works well @ this system
        """
        must_exit = dependency_check(dependency_set=CORE, exit_on_failure=False)
        self.assertFalse(must_exit)

    def test_default_platform_core_all_deps(self):
        """
        Test that the dependency check works for core + default platform when
        the dependencies are met.
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat:
            mock_curr_plat.return_value = DefaultPlatform()
            must_exit = dependency_check(dependency_set=CORE,
                                         exit_on_failure=False)
            self.assertFalse(must_exit)

    def test_default_platform_core_missing_deps(self):
        """
        Test that the dependency check works for core + default platform when
        there are missing PIP core dependencies.
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat,\
        patch('sys.stdout') as stdout_mock:
            default = DefaultPlatform()
            default.PIP_PACKAGES = default.PIP_PACKAGES.copy()
            default.PIP_PACKAGES[CORE] = default.PIP_PACKAGES[CORE][:]
            default.PIP_PACKAGES[CORE].append(self.fake_rumba_dependency)

            mock_curr_plat.return_value = default

            must_exit = dependency_check(dependency_set=CORE,
                                         exit_on_failure=False)
            self.assertTrue(must_exit)

            all_stdout = ''.join(k[1][0] for k in stdout_mock.method_calls)
            self.assertIn(self.MISSING_DEP_CMD, all_stdout)

    def test_default_platform_gui(self):
        """
        Test that the dependency check works for gui + default platform when the
        dependencies are met.
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat:
            mock_curr_plat.return_value = DefaultPlatform()
            must_exit = dependency_check(dependency_set=GUI,
                                         exit_on_failure=False)
            self.assertFalse(must_exit)

    def test_default_platform_gui_missing_deps(self):
        """
        Test that the dependency check works for gui + default platform when
        there are missing PIP core dependencies.
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat,\
        patch('sys.stdout') as stdout_mock:
            default = DefaultPlatform()
            default.PIP_PACKAGES = default.PIP_PACKAGES.copy()
            default.PIP_PACKAGES[GUI] = default.PIP_PACKAGES[GUI][:]
            default.PIP_PACKAGES[GUI].append(self.fake_rumba_dependency)

            mock_curr_plat.return_value = default

            must_exit = dependency_check(dependency_set=GUI,
                                         exit_on_failure=False)
            self.assertTrue(must_exit)

            all_stdout = ''.join(k[1][0] for k in stdout_mock.method_calls)
            self.assertIn(self.MISSING_DEP_CMD, all_stdout)

    def test_ubuntu1204_core(self):
        """
        Test that the dependency check works for core + ubuntu1204
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat:
            mock_curr_plat.return_value = Ubuntu1204()
            must_exit = dependency_check(dependency_set=CORE,
                                         exit_on_failure=False)
            self.assertFalse(must_exit)

    def test_ubuntu1204_gui(self):
        """
        Test that the dependency check works for core + ubuntu1204
        """
        with patch(self.CURR_PLATFORM) as mock_curr_plat:
            mock_curr_plat.return_value = Ubuntu1204()
            must_exit = dependency_check(dependency_set=GUI,
                                         exit_on_failure=False)
            self.assertFalse(must_exit)

