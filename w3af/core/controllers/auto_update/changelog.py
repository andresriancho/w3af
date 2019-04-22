"""
changelog.py

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
import git

from w3af.core.controllers.misc.home_dir import W3AF_LOCAL_PATH

ACTIONS = {'Added': 'A',
           'Deleted': 'D',
           'Renamed': 'R',
           'Modified': 'M',}

# Files statuses
ST_CONFLICT = 'C'
ST_NORMAL = 'N'
ST_UNVERSIONED = 'U'
ST_MODIFIED = 'M'
ST_UNKNOWN = '?'

# Limit of lines to SVNList types. To be used in __str__ method re-definition.
PRINT_LINES = 20

class Commit(object):
    """
    Wrapper around git.Commit for easy access to data.
    """
    def __init__(self, git_commit):
        self._git_commit = git_commit
        self._changes = []
    
    def add_change(self, action_short, filename):
        if action_short not in ACTIONS.values():
            raise ValueError('Action must be in ACTIONS.')
        
        self._changes.append((action_short, filename))
                             
    @property
    def commit_id(self):
        return self._git_commit.name_rev.split(' ')[0]
    
    @property
    def summary(self):
        return self._git_commit.summary
    
    @property
    def stats(self):
        return self._git_commit.stats.total

    @property
    def files(self):
        return self._git_commit.stats.files
    
    @property
    def changes(self):
        """
        self._changes holds (one of ACTIONS.values(), filename), for example:
            ('M', 'w3af_console')
            ('D', 'extlib/')
        """
        return self._changes
    
    def __str__(self):
        return '<Commit %s with %s file changes>' % (self.commit_id, len(self._changes))

def get_affected_file(file_diff):
    if file_diff.a_blob:
        affected_file = file_diff.a_blob.path
    elif file_diff.b_blob:           
        affected_file = file_diff.b_blob.path
        
    return affected_file

class ChangeLog(object):
    """
    Easy access to all changes performed between two commits in a branch.
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end
    
    def get_changes(self):
        changes = []
        
        crange = '%s..%s' % (self.start, self.end)
        
        for git_commit in git.Repo(W3AF_LOCAL_PATH).iter_commits(crange):
            commit = Commit(git_commit)
            
            diff = git_commit.parents[0].diff(git_commit)
            
            for action_short in ACTIONS.values():
                for file_diff in diff.iter_change_type(action_short):
                    affected_file = get_affected_file(file_diff)
                    commit.add_change(action_short, affected_file)
                    
            changes.append(commit)
        
        return changes
    
    def __str__(self):
        output = ''
        MAX_FILES = 15
        MAX_COMMITS = 10
        
        for commit in self.get_changes()[:MAX_COMMITS]:
            
            file_changes_str = ''
            for file_change in commit.changes[:MAX_FILES]:
                file_changes_str += '    %s %s\n' % (file_change[0],
                                                     file_change[1])
            
            if len(commit.changes) > MAX_FILES:
                more = (len(commit.changes)-MAX_FILES)
                file_changes_str += '    And %s files more...\n' % more 
            
            output += '%s: %s\n%s' % (commit.commit_id[:10],
                                      commit.summary[:100],
                                      file_changes_str)
        
        return output
            
            
    