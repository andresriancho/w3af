'''
utils.py

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
'''
import git

from core.controllers.misc.homeDir import W3AF_LOCAL_PATH

def to_short_id(commit_id):
    return commit_id[:10]

def is_git_repo(path=W3AF_LOCAL_PATH):
    '''
    Test whether current's w3af directory is a GIT repository.
    '''
    try:
        git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        return False
    else:
        return True
    
def get_latest_commit(path=W3AF_LOCAL_PATH):
    '''
    Summarize the local revision(s) of a `path`'s working copy.
    '''
    return git.Repo(path).head.commit.hexsha

def get_current_branch(path=W3AF_LOCAL_PATH):
    '''
    @return: The active branch for the repo at "path".
    
    Reminder about GitPython's output:
    
    >>> [ref.name for ref in git.Repo('.').refs if \
         ref.commit.hexsha == git.Repo('.').head.commit.hexsha]
    ['threading2', 'origin/threading2']
    >>> 
    '''
    repo = git.Repo(path)
    names = [ref.name for ref in repo.refs if ref.commit.hexsha == get_latest_commit()]
    name = [name for name in names if '/' not in name][0]
    return name
