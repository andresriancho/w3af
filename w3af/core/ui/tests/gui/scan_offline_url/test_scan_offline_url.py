"""
test_scan_offline_url.py

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


class TestScanOfflineURL(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'scan_offline_url', 'images')
    
    def test_scan_offline_url(self):
        self.click('owasp_top_10_profile')
        self.click('insert_target_url_here')
        self.type('http://moth:8181/', False)
        self.type(['<Enter>',], False)
        
        self.find('log_tab_enabled')
        self.find('clear_icon')
        self.find('connection_refused')
        
        
        