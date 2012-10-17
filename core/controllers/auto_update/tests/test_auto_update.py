'''
test_auto_update.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
import os

from mock import MagicMock, Mock, patch
from pysvn import wc_notify_action as wcna
from pysvn import Revision
from pysvn import wc_status_kind as wcsk
from collections import namedtuple
from nose.plugins.skip import SkipTest

import core.controllers.auto_update.auto_update as autoupdmod

from core.controllers.auto_update.auto_update import (
    w3afSVNClient, Revision, VersionMgr, SVNFilesList, StartUpConfig,
    FILE_UPD, FILE_NEW, FILE_DEL, ST_CONFLICT, ST_MODIFIED, ST_UNKNOWN,
    W3AF_LOCAL_PATH, get_svnversion, SVNError, SVNUpdateError
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
        self.client._svnclient = Mock()
        
        self.pysvn_client_patcher_side_effect = None
        self.pysvn_client_patcher = patch('pysvn.Client', side_effect=self.pysvn_client_patcher_side_effect)
        self.pysvn_client_mock = self.pysvn_client_patcher.start()
    
    def tearDown(self):
        self.pysvn_client_patcher.stop()
    
    def test_has_repourl(self):
        self.assertTrue(self.client._repourl is not None)

    def test_has_svn_client(self):
        self.assertTrue(self.client._svnclient is not None)

    def test_has_localpath(self):
        self.assertTrue(self.client._localpath is not None)

    def test_upd(self):
        client = self.client
        
        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)
        
        client._svnclient.update = MagicMock(return_value=self.rev)
        client._filter_files = MagicMock(return_value=self.upd_files)
        
        self.assertEquals(self.upd_files, client.update(rev=None))
        client._svnclient.update.assert_called_once_with(LOCAL_PATH, revision=pysvnhead, depth=INF)
        client._filter_files.assert_called_once_with(client.UPD_ACTIONS)
        
    def test_upd_fail(self):
        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)
        
        client = self.client
        client._svnclient.update = MagicMock(side_effect=pysvn.ClientError('file locked'))
 
        self.assertRaises(SVNUpdateError, client.update)
        client._svnclient.update.assert_called_once_with(LOCAL_PATH, revision=pysvnhead, depth=INF)
        
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
        os.path.isdir = MagicMock(return_value=False)
        
        # Call client's callback function several times
        f1 = '/path/to/file/foo.py'
        ev = {'action': wcna.update_delete,
               'error': None, 'mime_type': None,
               'path': f1,
               'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev)

        f2 = '/path/to/file/foo2.py'        
        ev2 = {'action': wcna.update_update,
               'error': None, 'mime_type': None,
               'path': f2,
               'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev2)
        
        expected_res = SVNFilesList([(f1, FILE_DEL), (f2, FILE_UPD)])
        self.assertEquals(expected_res, 
            client._filter_files(filterbyactions=w3afSVNClient.UPD_ACTIONS))

    def test_status(self):
        # Mock pysvnstatus objects
        smock1 = Mock()
        smock1.path = '/some/path/foo'
        smock1.text_status = wcsk.modified
        
        smock2 = Mock()
        smock2.path = '/some/path/foo2'
        smock2.text_status = wcsk.conflicted
        
        smock3 = Mock()
        smock3.path = '/some/path/foo3'
        smock3.text_status = 'some_weird_status'
        
        status_files = [smock1, smock2, smock3]
        client = w3afSVNClient(LOCAL_PATH)
        client._svnclient.status = MagicMock(return_value=status_files)
        
        expected_res = SVNFilesList([('/some/path/foo', ST_MODIFIED),
                                     ('/some/path/foo2', ST_CONFLICT),
                                     ('/some/path/foo3', ST_UNKNOWN)])
        self.assertEquals(expected_res, client.status())
    
    def test_not_working_copy(self):
        cli = Mock()
        cli.status = MagicMock(side_effect=Exception())
        self.pysvn_client_patcher_side_effect = [cli,]
        self.assertFalse( w3afSVNClient.is_working_copy(LOCAL_PATH) )
    
    def test_a_working_copy(self):
        cli = Mock()
        cli.status = MagicMock()
        self.pysvn_client_patcher_side_effect = [cli,]
        self.assertTrue(w3afSVNClient.is_working_copy(LOCAL_PATH))

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
        
        for freq, diffdays in ((SC.FREQ_DAILY, 1), (SC.FREQ_WEEKLY, 8), \
                               (SC.FREQ_MONTHLY, 34)):
            
            vmgr._start_cfg = start_cfg = StartUpConfig()
            start_cfg._autoupd = True
            start_cfg._freq = freq
            
            last_upd = datetime.date.today() - datetime.timedelta(days=diffdays)
            start_cfg._lastupd = last_upd
            
            self.assertTrue(vmgr._has_to_update())
    
    def test_added_new_dependencies(self):
        pass


class TestSVNVersion(unittest.TestCase):
    
    Rev = namedtuple('Rev', ('number',))
    
    def setUp(self):
        self.cli = Mock()
        pysvn.Client = MagicMock(return_value=self.cli)
    
    def test_get_svnversion_with_non_svn_path(self):
        def side_effect(path):
            for fake_data in [('x', 'y', 'z'),
                              ('x', 'y', 'z'),
                              ('x', 'y', 'z')]:
                yield fake_data
        os.walk = MagicMock(side_effect=side_effect)
        
        cli = self.cli
        Rev = TestSVNVersion.Rev
        cli.info = MagicMock(side_effect=[{'revision': Rev(22)},
                                          {'revision': Rev(23)},
                                          pysvn.ClientError()])
        
        self.assertEquals('22:23', get_svnversion(W3AF_LOCAL_PATH))
    
    def test_non_svn_install(self):
        '''
        Ensure that SVNError is raised when `get_svnversion` is called
        in a non svn copy.
        '''
        os.walk = MagicMock(return_value=[])
        with self.assertRaises(SVNError) as cm:
            get_svnversion(W3AF_LOCAL_PATH)
        self.assertTrue("is not a svn working copy" in cm.exception.message)
        
    