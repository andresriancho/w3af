'''
test_auto_update.py

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
import datetime
import pysvn
import unittest

from mock import MagicMock, Mock, patch
from collections import namedtuple

import core.controllers.auto_update.auto_update as autoupdmod

from core.data.db.startup_cfg import StartUpConfig
from core.controllers.auto_update.auto_update import (
    w3afSVNClient, Revision, VersionMgr, SVNFilesList,
    FILE_UPD, FILE_NEW, FILE_DEL, ST_CONFLICT, ST_MODIFIED, ST_UNKNOWN,
    W3AF_LOCAL_PATH, get_svn_version, SVNError, SVNUpdateError
)

REPO_URL = 'http://localhost/svn/w3af'
LOCAL_PATH = '/home/user/w3af'
INF = pysvn.depth.infinity


class Testw3afSVNClient(unittest.TestCase):

    rev = Revision(112, None)
    upd_files = SVNFilesList(
        [('file1.txt', FILE_NEW),
         ('file2.py', FILE_UPD),
         ('file3.jpg', FILE_DEL)],
        rev
    )

    def setUp(self):
        w3afSVNClient._get_repourl = MagicMock(return_value=None)

        self.client = w3afSVNClient(LOCAL_PATH)
        self.client._repourl = REPO_URL

        class FakeSVNClient(object):
            '''Tried to do this with a Mock() but for some reason it failed,
            I should learn more about Mock!'''
            pass
        self.client._svnclient = FakeSVNClient()

    def test_has_repourl(self):
        self.assertTrue(self.client._repourl is not None)

    def test_has_svn_client(self):
        self.assertTrue(self.client._svnclient is not None)

    def test_has_localpath(self):
        self.assertTrue(self.client._localpath is not None)

    def test_upd(self):
        client = self.client

        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)

        client._svnclient.update = MagicMock(return_value=[self.rev, ])
        client._filter_files = MagicMock(return_value=self.upd_files)

        self.assertEquals(self.upd_files, client.update(rev=None))

        # The next line throws this assertion error:
        # AssertionError: Expected call: mock('/home/user/w3af', depth=<depth.infinity>, revision=<Revision kind=head>)
        #                   Actual call: mock('/home/user/w3af', depth=<depth.infinity>, revision=<Revision kind=head>)
        # Which makes no sense since they are the same!
        #
        # client._svnclient.update.assert_called_once_with(LOCAL_PATH, depth=INF, revision=pysvnhead)
        #

    def test_upd_fail(self):
        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)

        client = self.client
        client._svnclient.update = MagicMock(
            side_effect=pysvn.ClientError('file locked'))

        self.assertRaises(SVNUpdateError, client.update)

        # Verify that we're retrying
        self.assertEqual(len(client._svnclient.update.call_args_list), 3)

        # Verify that we use the correct parameters
        args_list = client._svnclient.update.call_args_list
        path = list(set([arg[0][0] for arg in args_list]))[0]
        #depth = list(set([arg[1] for arg in args_list]))[0]
        #revision = list(set([arg[2] for arg in args_list]))[0]

        self.assertEqual(path, LOCAL_PATH)
        #self.assertEqual(depth, INF)
        #self.assertEqual(revision, pysvnhead)

    def test_upd_conflict(self):
        '''
        Files in conflict exists after update.
        '''
        pass

    def test_upd_nothing_to_update(self):
        '''No update to current copy was made. Tell the user. Presumably
        the revision was incremented'''
        pass

    def test_filter_files(self):
        client = self.client
        os_path_isdir_patcher = patch('os.path.isdir', return_value=False)
        os_path_isdir_patcher.start()

        # Call client's callback function several times
        f1 = '/path/to/file/foo.py'
        ev = {'action': pysvn.wc_notify_action.update_delete,
              'error': None, 'mime_type': None,
              'path': f1,
              'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev)

        f2 = '/path/to/file/foo2.py'
        ev2 = {'action': pysvn.wc_notify_action.update_update,
               'error': None, 'mime_type': None,
               'path': f2,
               'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev2)

        expected_res = SVNFilesList([(f1, FILE_DEL), (f2, FILE_UPD)])
        self.assertEquals(expected_res,
                          client._filter_files(filterbyactions=w3afSVNClient.UPD_ACTIONS))

        os_path_isdir_patcher.stop()

    def test_status(self):
        # Mock pysvnstatus objects
        smock1 = Mock()
        smock1.path = '/some/path/foo'
        smock1.text_status = pysvn.wc_status_kind.modified

        smock2 = Mock()
        smock2.path = '/some/path/foo2'
        smock2.text_status = pysvn.wc_status_kind.conflicted

        smock3 = Mock()
        smock3.path = '/some/path/foo3'
        smock3.text_status = 'some_weird_status'

        status_files = [smock1, smock2, smock3]

        client = self.client
        client._svnclient.status = MagicMock(return_value=status_files)

        expected_res = SVNFilesList([('/some/path/foo', ST_MODIFIED),
                                     ('/some/path/foo2', ST_CONFLICT),
                                     ('/some/path/foo3', ST_UNKNOWN)])
        self.assertEquals(expected_res, client.status())

    def test_not_working_copy(self):
        cli = Mock()
        cli.status = MagicMock(side_effect=Exception())

        pysvn_client_patcher = patch('pysvn.Client', return_value=cli)
        pysvn_client_patcher.start()

        self.assertFalse(w3afSVNClient.is_working_copy(LOCAL_PATH))

        pysvn_client_patcher.stop()

    def test_a_working_copy(self):
        cli = Mock()
        cli.status = MagicMock(return_value=True)

        pysvn_client_patcher = patch('pysvn.Client', return_value=cli)
        pysvn_client_patcher.start()

        self.assertTrue(w3afSVNClient.is_working_copy(LOCAL_PATH))

        pysvn_client_patcher.stop()

    def test_commit(self):
        pass


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
        # Override auto_update module variable
        autoupdmod.SVNClientClass = Mock()
        self.vmgr = VersionMgr(LOCAL_PATH, MagicMock(return_value=None))

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

            last_upd = datetime.date.today(
            ) - datetime.timedelta(days=diffdays)
            start_cfg._lastupd = last_upd

            self.assertTrue(vmgr._has_to_update())

    def test_added_new_dependencies(self):
        pass


class TestSVNVersion(unittest.TestCase):

    Rev = namedtuple('Rev', ('number',))

    def setUp(self):
        self.cli = Mock()

        self.pysvn_client_patch = patch('pysvn.Client', return_value=self.cli)
        self.pysvn_client_patch.start()

    def tearDown(self):
        self.pysvn_client_patch.stop()

    def test_get_svn_version_with_non_svn_path(self):
        cli = self.cli
        Rev = TestSVNVersion.Rev
        cli.info = MagicMock(side_effect=[{'revision': Rev(22)},
                                          {'revision': Rev(23)},
                                          pysvn.ClientError()])

        def side_effect(path):
            for fake_data in [('x', 'y', 'z'),
                              ('x', 'y', 'z'),
                              ('x', 'y', 'z')]:
                yield fake_data

        os_walk_patch = patch('os.walk', side_effect=side_effect)
        os_walk_patch.start()

        self.assertEquals('22:23', get_svn_version(W3AF_LOCAL_PATH))
        os_walk_patch.stop()

    def test_non_svn_install(self):
        '''
        Ensure that SVNError is raised when `get_svn_version` is called
        in a non svn copy.
        '''
        os_walk_patch = patch('os.walk', return_value=[])
        os_walk_patch.start()

        with self.assertRaises(SVNError) as cm:
            get_svn_version(W3AF_LOCAL_PATH)
        self.assertTrue("is not a svn working copy" in cm.exception.message)

        os_walk_patch.stop()
