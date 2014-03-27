"""
test_auto_update.py

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
import subprocess
import datetime
import sys

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest
from w3af.core.data.db.startup_cfg import StartUpConfig


class TestAutoUpdate(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'auto_update', 'images')

    def start_gui(self):
        """
        Need to override this method in order to avoid waiting for the "real"
        UI to load.
        """
        self.gui_process = subprocess.Popen([sys.executable, "w3af_gui", "-n"],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        self.gui_process_pid = self.gui_process.pid

    def tearDown(self):
        XpresserUnittest.tearDown(self)
        
        # Just in case... we don't want to break other tests
        startup_cfg = StartUpConfig()
        startup_cfg.last_upd = datetime.date.today()
        startup_cfg.save()
        
    def test_disclaimer_shown_accept(self):
        startup_cfg = StartUpConfig()
        startup_cfg.last_upd = datetime.date.today() - datetime.timedelta(days=3)
        startup_cfg.save()
        
        self.find('update_window')
        self.click('update')
        
        self.find('owasp_top_10_profile') 
