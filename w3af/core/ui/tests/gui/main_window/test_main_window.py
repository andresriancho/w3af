"""
test_main_window.py

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


class TestMainWindow(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'main_window', 'images')
    
    def test_main_menu(self):
        self.hover('main-window-title')
        self.find('main-window-menu')

    def test_profiles_loaded(self):
        self.find('owasp_top_10_profile')

    def test_plugins_loaded(self):
        self.find('audit_plugin_type')
        self.double_click('audit_plugin_type_text')
        self.find('eval_plugin')
        
        self.double_click('output_plugin_type_text')
        self.find('output_plugin_list')
    
    def test_tab_navigation(self):
        self.sleep(1)
        self.click('log_tab')
        self.find('scan_not_started')
        
        self.click('results_tab')
        self.find('scan_not_started')

        self.find('throbber_stopped')
        
        self.click('exploit_tab')
        self.find('exploit_list')
        