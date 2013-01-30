'''
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

'''
from core.controllers.auto_update.utils import (is_git_repo, to_short_id,
                                                get_latest_commit,
                                                get_latest_commit_date,)


def get_w3af_version():
    '''
    @return: A string with the w3af version.
    '''
    commit = to_short_id(get_latest_commit()) if is_git_repo() else 'unknown'
    cdate = ' - %s' % get_latest_commit_date() if is_git_repo() else ''
    
    return ('w3af - Web Application Attack and Audit Framework\n'
            'Version: 1.5\n'
            'Revision: %s%s\n'
            'Author: Andres Riancho and the w3af team.') % (commit,
                                                            cdate)
