"""
test_two_scans.py

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

from nose.plugins.skip import SkipTest

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest


class TestTwoScans(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'two_scans', 'images')
    
    SCAN_IMAGES_1 =  os.path.join(GUI_TEST_ROOT_PATH, 'exploit', 'images')
    SCAN_IMAGES_2 =  os.path.join(GUI_TEST_ROOT_PATH, 'new_profile', 'images')
    
    TARGET_1 = 'http://moth/w3af/audit/sql_injection/select/sql_injection_integer.php?id=1'
    TARGET_2 = 'http://moth/w3af/audit/xss/simple_xss.php?text=1'
    
    def setUp(self):
        super(TestTwoScans, self).setUp()
        
        self.xp.load_images(self.SCAN_IMAGES_1)
        self.xp.load_images(self.SCAN_IMAGES_2)
    
    def test_two_scans(self):
        raise SkipTest('See comment below in run_scan_2')
    
        self.run_scan_1()
        self.glue()
        self.run_scan_2()
        
    def run_scan_1(self):
        # Enable all audit plugins
        self.click('audit_plugin_checkbox')
        
        self.click('insert_target_url_here')
        self.type(self.TARGET_1, False)
        self.type(['<Enter>',], False)

        self.find('log_tab_enabled')
        self.find('sql_mysql', 25)

    def glue(self):
        # Wait for the scan to finish
        self.find('clear_icon', 20)
        self.click('clear_icon')

    def run_scan_2(self):
        self.double_click('previous_target')
        self.type(['<Home>'], False)
        for _ in xrange(len(self.TARGET_1)): self.type(['<Delete>'], False)

        # This type() seems to trigger the same bug I get in prompt.py:
        # https://github.com/andresriancho/w3af/issues/228
        self.type(self.TARGET_2, False)
        self.type(['<Tab>'], False)
        self.type(['<Enter>',], False)

        self.find('log_tab_enabled')
        self.find('clear_icon', 25)
        
        self.find('xss_vuln_in_log')