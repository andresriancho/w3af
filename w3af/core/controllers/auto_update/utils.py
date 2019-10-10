"""
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
"""
import git
import time

from w3af.core.controllers.misc.home_dir import W3AF_LOCAL_PATH

DETACHED_HEAD = 'detached HEAD'


def to_short_id(commit_id):
    return commit_id[:10]


def is_git_repo(path=W3AF_LOCAL_PATH):
    """
    Test whether current's w3af directory is a GIT repository.
    """
    try:
        git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        return False
    else:
        return True


def is_dirty_repo(path=W3AF_LOCAL_PATH):
    """
    :return: True if the repository is dirty (contains local changes)
    """
    try:
        repo = git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        return False
    else:
        return repo.is_dirty()


def get_latest_commit(path=W3AF_LOCAL_PATH):
    """
    :return: A string (hex sha) that identifies the commit
    """
    return git.Repo(path).head.commit.hexsha


def get_commit_id_date(commit_id, path=W3AF_LOCAL_PATH):
    """
    :return: The date for the @commit_id
    """
    heads = [ref.commit for ref in git.Repo(path).refs]
    
    for commit in heads:
        if commit.hexsha == commit_id:
            cdate = commit.committed_date
            return time.strftime("%d %b %Y %H:%M", time.gmtime(cdate))
    
    return None


def get_latest_commit_date(path=W3AF_LOCAL_PATH):
    """
    :return: The date for the latest commit
    """
    cdate = git.Repo(path).head.commit.committed_date
    return time.strftime("%d %b %Y %H:%M", time.gmtime(cdate)) 


def get_current_branch(path=W3AF_LOCAL_PATH):
    """
    :return: The active branch for the repo at "path".
    """
    repo = git.Repo(path)
    
    try:
        name = repo.active_branch.name
    except IndexError:
        return DETACHED_HEAD
    except TypeError:
        return DETACHED_HEAD

    return name


def repo_has_conflicts(path=W3AF_LOCAL_PATH):
    """
    :return: True if there was any merge conflict with the last pull()
    """
    for stage, _ in git.Repo(path).index.iter_blobs():
        if stage != 0:
            return True
    return False
