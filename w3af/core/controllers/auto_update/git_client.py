"""
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
"""
import threading
import weakref

import git

from git.util import RemoteProgress

from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.auto_update.changelog import ChangeLog
from w3af.core.controllers.auto_update.utils import (get_latest_commit,
                                                     get_current_branch,
                                                     repo_has_conflicts)


class GitClientError(Exception):
    pass


class GitClient(object):
    """
    Our wrapper for performing actions on the git repository.
    """
    UPD_ERROR_MSG = ('An error occurred while fetching from the remote'
                     ' Git repository! Please update manually using'
                     ' "git pull".')

    def __init__(self, path):
        self._actionlock = threading.RLock()
        self._repo = git.Repo(path)
        self._progress = GitRemoteProgress()
    
    def add_observer(self, observer):
        """
        :param observer: Function which takes four parameters,
                            op_code, cur_count, max_count, message
        """
        self._progress.add_observer(observer)
    
    @property
    def URL(self):
        return self._repo.remotes.origin.url

    @retry(tries=2, delay=0.5, backoff=2)
    def pull(self):
        with self._actionlock:
            try:
                latest_before_pull = get_latest_commit()
            
                self._repo.remotes.origin.pull(progress=self._progress)

                after_pull = get_latest_commit()
            
            # The developers at the mailing list were unable to tell me
            # if the pull() would raise an exception on merge conflicts
            # or which exception would be raised. So I'm catching all and
            # verifying if there are conflicts in an exception and in the
            # case were no exceptions were raised
            except Exception, e:
                self.handle_conflicts(latest_before_pull)
                msg = self.UPD_ERROR_MSG + ' The original exception was: "%s"'
                raise GitClientError(msg % e)
            else:
                self.handle_conflicts(latest_before_pull)
                changelog = ChangeLog(latest_before_pull, after_pull)
                return changelog

    #@retry(tries=2, delay=0.5, backoff=2)
    def fetch(self):
        with self._actionlock:
            try:
                self._repo.remotes.origin.fetch(progress=self._progress)
            except Exception:
                raise GitClientError(self.UPD_ERROR_MSG)

        return True
    
    def handle_conflicts(self, reset_commit_id):
        """
        This method verifies if the repository is in conflict and resolved it
        by performing a reset() to the previous commit-id.
        
        :param reset_commit_id: The commit id to reset to
        @raise GitClientError: To let the user know that the update failed
        """
        if repo_has_conflicts():
            self.reset_to_previous_state(reset_commit_id)
            raise GitClientError('A merge conflict was generated while trying'
                                 ' to update to the latest w3af version, please'
                                 ' update manually by using a git client.')
    
    def reset_to_previous_state(self, reset_commit_id):
        """
        Does a "git reset --hard <reset_commit_id>".
        
        :param reset_commit_id: The commit id to reset to
        """
        self._repo.head.reset(commit=reset_commit_id, index=True,
                              working_tree=True)
        
    def get_remote_head_id(self):
        """
        :return: The ID for the latest commit in the REMOTE repo.
        """
        # Get the latest changes from the remote end
        self.fetch()
        
        branch_origin = 'origin/%s' % get_current_branch()
        all_refs = self._repo.remotes.origin.refs
        origin_master = [ref for ref in all_refs if ref.name == branch_origin][0]
        
        return origin_master.commit.hexsha
        
    def get_local_head_id(self):
        """
        :return: The ID for the latest commit in the LOCAL repo.
        """
        branch_name = get_current_branch()
        repo_refs = self._repo.refs
        origin_master = [ref for ref in repo_refs if ref.name == branch_name][0]
        
        return origin_master.commit.hexsha
    
    def get_parent_for_revision(self, child_hexsha):
        """
        :return: The parent revision ID for the given hexsha.
        """
        result = []
        
        for commit in self._repo.iter_commits():
            if commit.hexsha == child_hexsha:
                result = [c.hexsha for c in commit.parents]
        
        return result
                
        
class GitRemoteProgress(RemoteProgress):
    """
    PythonGit will call update() on this object if I pass them to the progress
    parameter of pull or fetch in order to report progress on the long, network-
    bound task.
    """
    observers = []
    
    def add_observer(self, observer):
        self.observers.append(weakref.proxy(observer))
    
    def update(self, op_code, cur_count, max_count=None, message=''):
        for observer in self.observers: 
            observer(op_code, cur_count, max_count, message)
