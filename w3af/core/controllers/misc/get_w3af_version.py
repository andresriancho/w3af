"""
get_w3af_version.py

Copyright 2006 Andres Riancho

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
import os

from w3af import ROOT_PATH
from w3af.core.controllers.auto_update.utils import (is_git_repo, to_short_id,
                                                     get_latest_commit,
                                                     get_latest_commit_date,
                                                     get_current_branch,
                                                     is_dirty_repo)

VERSION_FILE = os.path.join(ROOT_PATH, 'core', 'data', 'constants', 'version.txt')


def get_minimalistic_version():
    return file(VERSION_FILE).read().strip()


def get_w3af_version():
    """
    :return: A string with the w3af version.
    """
    commit = to_short_id(get_latest_commit()) if is_git_repo() else 'unknown'
    cdate = ' - %s' % get_latest_commit_date() if is_git_repo() else ''
    branch = get_current_branch() if is_git_repo() else 'unknown'
    dirty = 'Yes' if is_dirty_repo() else 'No'

    vnumber = get_minimalistic_version()
    
    return ('w3af - Web Application Attack and Audit Framework\n'
            'Version: %s\n'
            'Revision: %s%s\n'
            'Branch: %s\n'
            'Local changes: %s\n'
            'Author: Andres Riancho and the w3af team.') % (vnumber, commit,
                                                            cdate, branch,
                                                            dirty)
