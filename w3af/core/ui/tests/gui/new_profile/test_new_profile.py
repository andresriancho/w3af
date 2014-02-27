"""
test_new_profile.py

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


class TestNewProfile(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'new_profile', 'images')
    EXTRA_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'scan_offline_url', 'images')
    TARGET_EVAL = 'http://moth/w3af/audit/eval/eval.php?c='
    
    def setUp(self):
        super(TestNewProfile, self).setUp()
        self.xp.load_images(self.EXTRA_IMAGES)
    
    def test_new_profile(self):
        self.click('new_profile')
        
        self.click('profile_name')
        self.type('test_profile', False)
        
        self.click('profile_description')
        self.type('test_profile_desc', False)
        
        self.click('profile_new_dlg_button')
        
        self.find('profile_desc_in_label')
        self.find('profile_disabled_all')
        self.find('profile_disabled_output')
        
        self.double_click('audit_plugin_type_text')
        
        # Note that this requires xpresser.ini to click on the right place
        # This enables the eval plugin
        self.click('eval_plugin')
        
        # Verify that the profile name is bold after the change
        self.find('bold_test_profile')
        
        self.click('profile_save')
        
        self.click('insert_target_url_here')
        self.type(self.TARGET_EVAL, False)
        self.type(['<Enter>',], False)

        # Verify that the profile name is bold after the change
        self.find('bold_test_profile')

        self.click('profile_save')
        
        self.find('log_tab_enabled')
        self.find('clear_icon', 25)
        
        self.click('scan_config')
        
        self.right_click('test_profile_selected')
        self.click('context_menu_profile_delete')
        self.click('yes')
        
        self.sleep(1)
        self.not_find('test_profile')
       
        
        