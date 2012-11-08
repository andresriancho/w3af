'''
test_helloworld.py

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

from mock import Mock

from core.ui.gui.tests.mocked.utils import refresh_gui
from core.ui.gui.tests.mocked.check_called import CheckCalled

from core.ui.gui.tests.helloworld import HelloWorld

class TestHelloWorld(unittest.TestCase):
    
    def test_get_instance(self):
        HelloWorld()

    def test_title_is_correct(self):
        hw = HelloWorld()
        self.assertEqual( hw.window.get_title(), 'helloworld.py')
        
    def test_click_button(self):
        hw = HelloWorld()
        
        mock_signal_hldr = Mock()
        hw.button.connect('clicked', mock_signal_hldr)
        
        hw.button.clicked()
        refresh_gui()
        
        print dir(mock_signal_hldr)
        mock_signal_hldr.a()
        print mock_signal_hldr.call_count