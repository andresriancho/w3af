"""
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
"""
import gc
import unittest
import datetime

from nose.plugins.attrib import attr
from mock import MagicMock

from w3af.core.data.db.startup_cfg import StartUpConfig
from w3af.core.controllers.auto_update.version_manager import VersionMgr
from w3af.core.controllers.auto_update.changelog import ChangeLog
from w3af.core.controllers.misc.home_dir import W3AF_LOCAL_PATH
from w3af.core.controllers.auto_update.git_client import GitClient


class TestVersionMgr(unittest.TestCase):

    def setUp(self):
        """
        Given that nosetests test isolation is "incompatible" with w3af's
        kb, cf, etc. objects, and the tests written here are overwriting
        some classes that are loaded into sys.modules and then used in other
        code sections -and tests-, I need to clean the mess after I finish.

        @see: http://mousebender.wordpress.com/2006/12/07/test-isolation-in-nose/

        I haven't been able to fix this issue... so I'm skipping these two
        tests!
        """
        self.vmgr = VersionMgr(W3AF_LOCAL_PATH, MagicMock(return_value=None))

    def test_no_need_update(self):
        vmgr = self.vmgr
        vmgr._start_cfg = StartUpConfig()
        vmgr._start_cfg._autoupd = False

        # Test no auto-update
        self.assertFalse(vmgr._has_to_update())

    def test_has_to_update(self):
        """
        Test [D]aily, [W]eekly and [M]onthly auto-update
        """
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

    def test_update_not_required_not_forced(self):
        """
        Test that we don't perform any extra steps if the local installation
        was already updated today.
        """
        self.vmgr._start_cfg = start_cfg = StartUpConfig()
        start_cfg._autoupd = True
        start_cfg._freq = StartUpConfig.FREQ_DAILY

        last_upd = datetime.date.today() - datetime.timedelta(days=0)
        start_cfg._lastupd = last_upd

        on_update_check_mock = MagicMock()
        on_already_latest_mock = MagicMock()
        on_update_mock = MagicMock()

        self.vmgr.register(VersionMgr.ON_UPDATE_CHECK, on_update_check_mock, None)
        self.vmgr.register(VersionMgr.ON_ALREADY_LATEST, on_already_latest_mock, None)
        self.vmgr.register(VersionMgr.ON_UPDATE, on_update_mock, None)

        self.vmgr.update()
        
        self.assertEqual(on_update_check_mock.call_count, 0)
        self.assertEqual(on_already_latest_mock.call_count, 0)
        self.assertEqual(on_update_mock.call_count, 0)

    @attr('ci_fails')
    def test_update_required_not_forced(self):
        """
        Test that we check if we're on the latest version if the latest
        local installation update was 3 days ago and the frequency is set to
        daily.
        
        The local repository is in the latest version (git pull is run before)

        In CircleCI this fails with the following message:
            You asked to pull from the remote 'origin', but did not specify
            a branch. Because this is not the default configured remote
            for your current branch, you must specify a branch on the command
            line.
        """
        git_client = GitClient('.')
        git_client.pull()
        
        self.vmgr._start_cfg = start_cfg = StartUpConfig()
        start_cfg._autoupd = True
        start_cfg._freq = StartUpConfig.FREQ_DAILY

        last_upd = datetime.date.today() - datetime.timedelta(days=3)
        start_cfg._lastupd = last_upd

        on_update_check_mock = MagicMock()
        on_already_latest_mock = MagicMock()
        on_update_mock = MagicMock()

        self.vmgr.register(VersionMgr.ON_UPDATE_CHECK, on_update_check_mock, None)
        self.vmgr.register(VersionMgr.ON_ALREADY_LATEST, on_already_latest_mock, None)
        self.vmgr.register(VersionMgr.ON_UPDATE, on_update_mock, None)

        self.vmgr.update()
        
        self.assertEqual(on_update_check_mock.call_count, 1)
        self.assertEqual(on_already_latest_mock.call_count, 1)
        self.assertEqual(on_update_mock.call_count, 0)
        
    @attr('ci_fails')
    def test_update_required_outdated_not_forced(self):
        """
        Test that we check if we're on the latest version if the latest
        local installation update was 3 days ago and the frequency is set to
        daily.
        
        The local repository is NOT in the latest version. A 'git reset --hard'
        is run at the beginning of this test to reset the repo to a revision
        before the latest one.

        *****   WARNING     *****
        *****   WARNING     *****

        YOU DON'T WANT TO RUN THIS TEST WITH OTHERS SINCE IT WILL BREAK THEM!

        *****   WARNING     *****
        *****   WARNING     *****
        """
        try:
            git_client = GitClient('.')
            head_id = git_client.get_local_head_id()
            one_before_head = git_client.get_parent_for_revision(head_id)
            git_client.reset_to_previous_state(one_before_head)
            
            self.vmgr._start_cfg = start_cfg = StartUpConfig()
            start_cfg._autoupd = True
            start_cfg._freq = StartUpConfig.FREQ_DAILY
    
            last_upd = datetime.date.today() - datetime.timedelta(days=3)
            start_cfg._lastupd = last_upd
    
            on_update_check_mock = MagicMock()
            on_already_latest_mock = MagicMock()
            on_update_mock = MagicMock()
    
            self.vmgr.register(VersionMgr.ON_UPDATE_CHECK, on_update_check_mock, None)
            self.vmgr.register(VersionMgr.ON_ALREADY_LATEST, on_already_latest_mock, None)
            self.vmgr.register(VersionMgr.ON_UPDATE, on_update_mock, None)

            self.vmgr.callback_onupdate_confirm = MagicMock(side_effect=[True,])
    
            self.vmgr.update()
            
            self.assertEqual(on_update_check_mock.call_count, 1)
            self.assertEqual(on_already_latest_mock.call_count, 0)
            self.assertEqual(on_update_mock.call_count, 1)
        finally:
            git_client.pull()

    def test_no_cycle_refs(self):
        vmgr = VersionMgr(W3AF_LOCAL_PATH, MagicMock(return_value=None))
        self.assertEqual(len(gc.get_referrers(vmgr)), 1)
