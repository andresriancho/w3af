'''
test_manual_requests.py

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
import os

from core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest


class TestManualRequests(XpresserUnittest):
    
    IMAGES = os.path.join('core', 'ui', 'tests', 'gui', 'manual_requests', 'images')
    EXTRA_IMAGES = os.path.join('core', 'ui', 'tests', 'gui', 'tools_menu', 'images')
    
    TEST_PORT = 8081
    
    def setUp(self):
        XpresserUnittest.setUp(self)
        self.click('manual-request')

    def tearDown(self):
        self.click('close-with-cross')
        XpresserUnittest.tearDown(self)
    
    def test_offline_url(self):
        self.double_click('localhost')
        self.type('moth:8081', False)
        
        self.click('send')
        self.find('stopped_sending_requests')
        
        # Close the error dialog
        self.type(['<Enter>',], False)
    