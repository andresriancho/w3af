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
    UPD_ERROR_MSG = ('An error occurred while fetching from the remote'
                     ' Git repository! Please update manually using'
                     ' "git pull".')

    def __init__(self, localpath):
        self._actionlock = threading.RLock()
        self._repo = git.Repo(localpath)

    @property
    def URL(self):
        return self._repo.remotes.origin.url

    @retry(tries=3, delay=0.5, backoff=2, exc_class=GitClientError,
           err_msg=UPD_ERROR_MSG)
    def pull(self, commit_id=None):
        with self._actionlock:
            
            latest_before_pull = get_latest_commit()
            
            # TODO: Use commit_id somewhere!
            self._repo.remotes.origin.pull()

            after_pull = get_latest_commit()

            changelog = ChangeLog(latest_before_pull, after_pull)
            return changelog

    @retry(tries=3, delay=0.5, backoff=2, exc_class=GitClientError,
           err_msg=UPD_ERROR_MSG)
    def fetch(self, commit_id=None):
        self._repo.remotes.origin.fetch()
        return True
    
    def get_remote_head_id(self):
        '''
        @return: The ID for the latest commit in the REMOTE repo.
        '''
        # Get the latest changes from the remote end
        self.fetch()

        # TODO: How could we manage branches? If the user is sitting in a branch
        # he expects to get updates from that branch, not from master, 'origin/master'
        # should be replaced by the current branch
        
        all_refs = self._repo.remotes.origin.refs
        origin_master = [ref for ref in all_refs if ref.name == 'origin/master'][0]
        
        return origin_master.commit.hexsha
        
    def get_local_head_id(self):
        '''
        @return: The ID for the latest commit in the LOCAL repo.
        '''
        # TODO: How could we manage branches? If the user is sitting in a branch
        # he expects to get updates from that branch, not from 'master'
        
        repo_refs = self._repo.refs
        origin_master = [ref for ref in repo_refs if ref.name == 'master'][0]
        
        return origin_master.commit.hexsha
        
    def _register(self, event):
        '''
        Callback method. Registers all events taking place during this action.
        '''
        self._events.append(event)