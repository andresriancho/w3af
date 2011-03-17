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

from pymock import PyMockTestCase, method, override, dontcare, set_count
import pysvn

from core.controllers.auto_update.auto_update import w3afSVNClient, Revision,\
    VersionMgr, SVNFilesList, StartUpConfig, FILE_UPD, FILE_NEW, FILE_DEL, \
    ST_CONFLICT, ST_MODIFIED, ST_UNKNOWN
from core.controllers import auto_update

# Remove magic method as it generates some conficts with pymock
del w3afSVNClient.__getattribute__
del VersionMgr.__getattribute__

REPO_URL = 'http://localhost/svn/w3af'
LOCAL_PATH = '/home/user/w3af'


def dummy(*args, **kwargs):
    pass


class Testw3afSVNClient(PyMockTestCase):
    
    rev = Revision(112, None)
    upd_files = SVNFilesList(
        [('file1.txt', FILE_NEW),
         ('file2.py', FILE_UPD),
         ('file3.jpg', FILE_DEL)],
         rev
        )

    def setUp(self):
        PyMockTestCase.setUp(self)
        
        w3afSVNClient._get_repourl = dummy
        self.client = w3afSVNClient(LOCAL_PATH)
        self.client._repourl = REPO_URL
        self.client._svnclient = self.mock()

    def test_has_repourl(self):
        self.assertTrue(self.client._repourl is not None)

    def test_has_svn_client(self):
        self.assertTrue(self.client._svnclient is not None)

    def test_has_localpath(self):
        self.assertTrue(self.client._localpath is not None)

    def test_upd(self):
        client = self.client
        override(pysvn, 'Revision', self.mock())
        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)
        method(client._svnclient, 'update').expects(LOCAL_PATH, revision=pysvnhead).returns([self.rev])
        override(client, '_filter_files').expects(client.UPD_ACTIONS)
        self.returns(self.upd_files)
        
        ## Stop recording. Play!
        self.replay()
        self.assertEquals(self.upd_files, client.update(rev=None))
        
        ## Verify ##
        self.verify()

    def test_upd_fail(self):
        override(pysvn, 'Revision', self.mock())
        pysvnhead = pysvn.Revision(pysvn.opt_revision_kind.head)
        from core.controllers.auto_update.auto_update import SVNUpdateError
        client = self.client
        method(client._svnclient, 'update').expects(LOCAL_PATH, revision=pysvnhead)
        self.raises(pysvn.ClientError('file locked'))
        
        ## Stop recording. Play!
        self.replay()
        self.assertRaises(SVNUpdateError, client.update)
        
        ## Verify ##
        self.verify()
        
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
        from pysvn import wc_notify_action as wcna
        from pysvn import Revision
        from core.controllers.auto_update.auto_update import os
        client = self.client
        override(os.path, 'isdir').expects(dontcare()).returns(False)
        set_count(exactly=2)
        ## Stop recording. Play!
        self.replay()
        # Call client's callback function several times
        f1 = '/path/to/file/foo.py'
        ev = {'action': wcna.update_delete,
               'error': None, 'mime_type': None, 'path': f1,
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
        ## Verify ##
        self.verify()

    def test_status(self):
        from pysvn import wc_status_kind as wcsk
        client = self.client
        # Mock pysvnstatus objects
        smock = self.mock()
        smock.path
        self.setReturn('/some/path/foo')
        smock.text_status
        self.setReturn(wcsk.modified)
        
        smock2 = self.mock()
        smock2.path
        self.setReturn('/some/path/foo2')
        smock2.text_status
        self.setReturn(wcsk.conflicted)
        
        smock3 = self.mock()
        smock3.path
        self.setReturn('/some/path/foo3')
        smock3.text_status
        self.setReturn('some_weird_status')
        
        status_files = [smock, smock2, smock3]
        method(client._svnclient, 'status').expects(LOCAL_PATH, recurse=False)
        self.returns(status_files)
        ## Stop recording - Replay ##
        self.replay()
        expected_res = \
            SVNFilesList([
                ('/some/path/foo', ST_MODIFIED),
                ('/some/path/foo2', ST_CONFLICT),
                ('/some/path/foo3', ST_UNKNOWN)])
        self.assertEquals(expected_res, client.status())
        ## Verify ##
        self.verify()
    
    def test_working_copy(self):

        cli = self.mock()
        override(pysvn, 'Client').expects().returns(cli)
        
        # NOT A WORKING COPY
        method(cli, 'status').expects(LOCAL_PATH, recurse=False).raises(Exception())
        self.replay()
        self.assertFalse(w3afSVNClient.is_working_copy(LOCAL_PATH))
        
        # IS A WORKING COPY
        self.reset()
        cli = self.mock()
        override(pysvn, 'Client').expects().returns(cli)
        method(cli, 'status').expects(LOCAL_PATH, recurse=False).returns(1)
        self.replay()
        self.assertTrue(w3afSVNClient.is_working_copy(LOCAL_PATH))

    def test_commit(self):
        pass


class TestVersionMgr(PyMockTestCase):
    
    def setUp(self):
        PyMockTestCase.setUp(self)
        # Override auto_update module variable
        import core.controllers.auto_update.auto_update as autoupdmod
        autoupdmod.SVNClientClass = self.mock()
        self.vmgr = VersionMgr(LOCAL_PATH, dummy)
    
    def test_has_to_update(self):
        
        vmgr = self.vmgr
        start_cfg_mock = self.mock()
        vmgr._start_cfg = start_cfg_mock
        
        # Test no auto-update
        start_cfg_mock.auto_upd
        self.setReturn(False)
        self.replay()
        self.assertFalse(vmgr._has_to_update())

        # Test [D]aily, [W]eekly and [M]onthly auto-update
        import datetime
        SC = StartUpConfig        
        for freq, diffdays in ((SC.FREQ_DAILY, 1), (SC.FREQ_WEEKLY, 8), \
                               (SC.FREQ_MONTHLY, 34)):
            self.reset()
            start_cfg_mock.auto_upd
            self.setReturn(True)
            start_cfg_mock.freq
            self.setReturn(freq)
            start_cfg_mock.last_upd
            self.setReturn(datetime.date.today() - datetime.timedelta(days=diffdays))
            self.replay()
            self.assertTrue(vmgr._has_to_update())
    
    def test_added_new_dependencies(self):
        pass
