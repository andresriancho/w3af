"""
test_no_plugins_scan.py

Copyright 2013 Andres Riancho

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

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest


class TestNoPluginsScan(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'no_plugins_scan', 'images')
    
    def test_no_plugins_enabled(self):
        self.click('insert_target_url_here')
        self.type('http://moth/', False)
        self.type(['<Enter>',], False)
        # For some reason this moves the mouse pointer to the right location
        # but then it doesn't seem to click on it
        #self.click('scan_start')
        
        self.find('no_plugins')
        self.click('ok')
        
        
        