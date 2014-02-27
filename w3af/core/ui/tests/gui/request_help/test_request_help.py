"""
test_request_help.py

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


class TestRequestHelp(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'request_help', 'images')
    
    def test_main_menu_help(self):
        # Make sure the focus is on the w3af_gui before we hit F1
        self.click('insert_target_url_here')
        
        self.type(['<F1>'], False)
        self.find('configuring_the_scan_fragment')
        
        # Close the browser tab we just opened
        #self.type(['<Ctrl>', 'W'], False)
        #self.sleep(1)
        
        # Come back from the browser to w3af
        self.type(['<Alt>', '<Tab>'], False)
        