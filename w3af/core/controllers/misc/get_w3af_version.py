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
from w3af.core.controllers.misc.decorators import memoized
from w3af.core.controllers.auto_update.utils import (is_git_repo, to_short_id,
                                                     get_latest_commit,
                                                     get_latest_commit_date,
                                                     get_current_branch,
                                                     is_dirty_repo)

VERSION_FILE = os.path.join(ROOT_PATH, 'core', 'data', 'constants',
                            'version.txt')


def get_minimalistic_version():
    return file(VERSION_FILE).read().strip()


@memoized
def get_w3af_version_as_dict():
    """
    This method seems to take considerable time to run when w3af is run from
    a git installation (.git directory is present). All of the time it takes
    to solve this function comes from get_w3af_version_as_dict(), which
    reads the Git meta-data.

    Some plugins, such as xml_file, call get_w3af_version every N seconds to
    write that information to the output file. I added @memoized in order to
    reduce the time it takes to run the output plugin.

    :return: All the version information in a dict
    """
    commit = to_short_id(get_latest_commit()) if is_git_repo() else 'unknown'
    cdate = ' - %s' % get_latest_commit_date() if is_git_repo() else ''
    branch = get_current_branch() if is_git_repo() else 'unknown'
    dirty = 'Yes' if is_dirty_repo() else 'No'

    return {'version': get_minimalistic_version(),
            'revision': commit + cdate,
            'branch': branch,
            'dirty': dirty}


def get_w3af_version():
    """
    :return: A string with the w3af version.
    """
    version_dict = get_w3af_version_as_dict()
    
    return ('w3af - Web Application Attack and Audit Framework\n'
            'Version: %(version)s\n'
            'Revision: %(revision)s\n'
            'Branch: %(branch)s\n'
            'Local changes: %(dirty)s\n'
            'Author: Andres Riancho and the w3af team.') % version_dict


def get_w3af_version_minimal():
    """
    :return: A string with the w3af version.
    """
    version_dict = get_w3af_version_as_dict()
    return '%(version)s / %(revision)s / %(branch)s' % version_dict
