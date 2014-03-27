"""
test_export_request.py

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


class TestExportRequest(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'export_request', 'images')
    EXTRA_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'tools_menu', 'images')
    
    def test_export_request_python(self):
        self.find('all-menu')
        self.click('export-http-icon')

        self.find('http_request_text')
        
        self.click('drop_down_export')
        self.click('python_export')
        self.click('export')
        
        self.find('python_code')
        
        # TODO: Click on this, save the file, assert the file contents
        self.find('save_request_as')
        
        self.click('close-with-cross')
