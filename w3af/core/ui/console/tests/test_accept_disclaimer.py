"""
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

from mock import patch, Mock

from w3af.core.ui.console.console_ui import ConsoleUI


class TestAcceptDisclaimer(unittest.TestCase):

    def setUp(self):
        self.console_ui = ConsoleUI(do_upd=False)

    class dummy_true(Mock):
        accepted_disclaimer = True

    class dummy_false(Mock):
        accepted_disclaimer = False

    @patch('w3af.core.ui.console.console_ui.StartUpConfig', new_callable=dummy_false)
    @patch('__builtin__.raw_input', return_value='')
    def test_not_saved_not_accepted(self, mocked_startup_cfg, mocked_input):
        self.assertFalse(self.console_ui.accept_disclaimer())

    @patch('w3af.core.ui.console.console_ui.StartUpConfig', new_callable=dummy_false)
    @patch('__builtin__.raw_input', return_value='y')
    def test_not_saved_accepted(self, mocked_startup_cfg, mocked_input):
        self.assertTrue(self.console_ui.accept_disclaimer())

    @patch('w3af.core.ui.console.console_ui.StartUpConfig', new_callable=dummy_true)
    def test_saved(self, mocked_startup_cfg):
        self.assertTrue(self.console_ui.accept_disclaimer())
