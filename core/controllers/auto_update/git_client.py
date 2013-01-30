'''
auto_update.py

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
import threading
import git
import os

from core.controllers.misc.decorators import retry
from core.controllers.auto_update.utils import get_latest_commit
from core.controllers.auto_update.changelog import ChangeLog


class GitClientError(Exception):
    pass


class GitClient(object):
    '''
    Our wrapper for performing actions on the git repository.
    '''
    UPD_ERROR_MSG = ('A repeated error occurred while updating from the '
                     'GIT Repo! Please update manually using "git pull".')

    def __init__(self, localpath):
        self._actionlock = threading.RLock()
        self._repo = git.Repo(localpath)

    @property
    def URL(self):
        return self._repo.remotes.origin.url

    @retry(tries=3, delay=0.5, backoff=2,
           exc_class=GitClientError,
           err_msg=UPD_ERROR_MSG)
    def pull(self, rev=None):
        with self._actionlock:
            
            latest_before_pull = get_latest_commit()
            
            self._repo.remotes.origin.pull()

            after_pull = get_latest_commit()

            changelog = ChangeLog(latest_before_pull, after_pull)
            return changelog

    def list(self, path_or_url=None, recurse=False):
        with self._actionlock:
            if not path_or_url:
                path_or_url = self._localpath
            entries = self._svnclient.list(path_or_url, recurse=recurse)
            res = [(ent.path, None) for ent, _ in entries]
            return SVNFilesList(res)

    def diff(self, localpath, rev=None):
        with self._actionlock:
            path = os.path.join(self._localpath, localpath)
            # If no rev is passed then compare to HEAD
            if rev is None:
                rev = pysvn.Revision(pysvn.opt_revision_kind.head)
            tempfile = os.tempnam()
            diff_str = self._svnclient.diff(tempfile, path, revision1=rev)
            return diff_str

    def log(self, start_rev, end_rev):
        '''
        Return SVNLogList of log messages between `start_rev`  and `end_rev`
        revisions.

        @param start_rev: Revision object
        @param end_rev: Revision object
        '''
        with self._actionlock:
            # Expected by pysvn.Client.log method
            _startrev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                       start_rev.number)
            _endrev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                     end_rev.number)
            logs = (l.message for l in self._svnclient.log(self._localpath,
                                                           revision_start=_startrev, revision_end=_endrev))
            rev = end_rev if (end_rev.number > start_rev.number) else start_rev
            return SVNLogList(logs, rev)

    @staticmethod
    def is_git_repo(localpath):
        try:
            pysvn.Client().status(localpath, recurse=False)
        except Exception:
            return False
        else:
            return True

    def _get_repourl(self):
        '''
        Get repo's URL.
        '''
        svninfo = self._get_svn_info(self._localpath)
        return svninfo.URL

    def _get_svn_info(self, path_or_url):
        try:
            return self._svnclient.info2(path_or_url, recurse=False)[0][1]
        except pysvn.ClientError, ce:
            raise SVNUpdateError(*ce.args)

    def get_revision(self, local=True):
        '''
        Return Revision object.

        @param local: If true return local's revision data; otherwise use
        repo's.
        '''
        path_or_url = self._localpath if local else self._repourl
        _rev = self._get_svn_info(path_or_url).rev
        return Revision(_rev.number, _rev.date)

    def _register(self, event):
        '''
        Callback method. Registers all events taking place during this action.
        '''
        self._events.append(event)