"""
test_click_menu.py

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


class ClickMenu(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'tools_menu', 'images')
    
    def test_click_menu(self):
        self.find('all-menu')
        self.click('manual-request')
        self.find('manual-request-request-response')
        self.find('manual-requests-window-title')
        self.click('close-with-cross')

        self.find('all-menu')
        self.click('fuzzy-requests-icon')
        self.find('fuzzy-requests-tabs')
        self.find('fuzzy-requests-window-title')
        self.click('close-with-cross')
        self.find('all-menu')

        self.find('all-menu')
        self.click('encode-decode-icon')
        self.find('encode-decode-window-title')
        self.find('encode-decode-encode-url')
        self.find('encode-decode-decode-url')
        self.click('close-with-cross')
        self.find('all-menu')

        self.find('all-menu')
        self.click('export-http-icon')
        self.find('export-http-window-title')
        self.find('export-http-export-html')
        self.click('close-with-cross')
        self.find('all-menu')

        self.find('all-menu')
        self.click('compare-icon')
        self.find('compare-window-title')
        self.click('close-with-cross')
        self.find('all-menu')

        self.find('all-menu')
        self.click('proxy-menu-icon')
        self.find('proxy-window-title')
        self.find('proxy-tabs')
        self.click('close-with-cross')
        self.click('yes')
        self.find('all-menu')
