'''
test_version_manager.py

Copyright 2011 Andres Riancho

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
import unittest
import datetime

from mock import MagicMock

from core.data.db.startup_cfg import StartUpConfig
from core.controllers.auto_update.version_manager import VersionMgr
from core.controllers.auto_update.changelog import ChangeLog
from core.controllers.misc.homeDir import W3AF_LOCAL_PATH


class TestVersionMgr(unittest.TestCase):

    def setUp(self):
        '''
        Given that nosetests test isolation is "incompatible" with w3af's
        kb, cf, etc. objects, and the tests written here are overwriting
        some classes that are loaded into sys.modules and then used in other
        code sections -and tests-, I need to clean the mess after I finish.

        @see: http://mousebender.wordpress.com/2006/12/07/test-isolation-in-nose/

        I haven't been able to fix this issue... so I'm skipping these two
        tests!
        '''
        self.vmgr = VersionMgr(W3AF_LOCAL_PATH, MagicMock(return_value=None))

    def test_no_need_update(self):
        vmgr = self.vmgr
        vmgr._start_cfg = StartUpConfig()
        vmgr._start_cfg._autoupd = False

        # Test no auto-update
        self.assertFalse(vmgr._has_to_update())

    def test_has_to_update(self):
        '''
        Test [D]aily, [W]eekly and [M]onthly auto-update
        '''
        SC = StartUpConfig
        vmgr = self.vmgr

        for freq, diffdays in ((SC.FREQ_DAILY, 1), (SC.FREQ_WEEKLY, 8),
                               (SC.FREQ_MONTHLY, 34)):

            vmgr._start_cfg = start_cfg = StartUpConfig()
            start_cfg._autoupd = True
            start_cfg._freq = freq

            last_upd = datetime.date.today() - datetime.timedelta(days=diffdays)
            start_cfg._lastupd = last_upd

            self.assertTrue(vmgr._has_to_update())

    def test_added_new_dependencies(self):
        start = 'cb751e941bfa2063ebcef711642ed5d22ff9db87'
        end = '9c5f5614412dce67ac13411e1eebd754b4c6fb6a'
        
        changelog = ChangeLog(start, end)
        
        self.assertTrue(self.vmgr._added_new_dependencies(changelog))
        
    def test_not_added_new_dependencies(self):
        start = '479f30c95873c3e4f8370ceb91f8aeb74794d047'
        end = '87924241bf70c2321bc9f567e3d2ce62ee264fee'
        
        changelog = ChangeLog(start, end)
        
        self.assertFalse(self.vmgr._added_new_dependencies(changelog))

