'''
xpresser_unittest.py

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
'''
import time
import os

from core.ui.tests.xpresser_wrapper.xpresser_unittest import XpresserUnittest


class ClickMenu(XpresserUnittest):
    
    IMAGES = os.path.join('core', 'ui', 'tests', 'menu', 'images')
    
    def test_click_menu(self):
        self.xp.find('all-menu')
        self.xp.click('manual-request')
        self.xp.find('manual-request-request-response')
        self.xp.find('manual-requests-window-title')
        self.xp.click('close-with-cross')
        self.xp.find('all-menu')
