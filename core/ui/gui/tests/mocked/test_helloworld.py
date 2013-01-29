'''
test_helloworld.py

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
import unittest

from mock import patch

from core.ui.gui.tests.helloworld import HelloWorld


class TestHelloWorld(unittest.TestCase):

    def test_get_instance(self):
        HelloWorld()

    def test_title_is_correct(self):
        hw = HelloWorld()
        self.assertEqual(hw.window.get_title(), 'helloworld.py')

    def test_click_button(self):
        module = 'core.ui.gui.tests.helloworld.%s'
        with patch(module % 'gtk.main_quit') as main_quit_mock:
            with patch(module % 'HelloWorld.hello') as hello_mock:
                hw = HelloWorld()
                hw.button.clicked()
                self.assertEqual(hw.window.get_title(), 'helloworld.py')
                self.assertTrue(hello_mock.called)
                self.assertTrue(main_quit_mock.called)

                # Still haven't found the need to use this one...
                # refresh_gui()
