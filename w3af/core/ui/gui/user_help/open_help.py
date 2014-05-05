"""
open_help.py

Copyright 2014 Andres Riancho

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
import webbrowser
import git

from w3af.core.controllers.auto_update.utils import (get_current_branch,
                                                     DETACHED_HEAD)


DOC_ROOT_FMT = 'http://docs.w3af.org/en/%s/gui/'
DOC_ROUTER = {
              'wizards': 'tools.html#wizards',
              'fuzzy_requests': 'tools.html#fuzzy-requests',
              'using_the_proxy': 'tools.html#using-the-proxy',
              'manual_requests': 'tools.html#manual-requests',
              'browsing_the_knowledge_base': 'analyzing-results.html#browsing-the-knowledge-base',
              # TODO: missing documentation for export requests
              #'export_requests': '',
              'encode_and_decode': 'tools.html#encode-and-decode',
              'cluster': 'tools.html?highlight=cluster#fuzzy-requests',
              'comparing_http_traffic': 'tools.html#comparing-http-traffic',
              'configuring_the_scan': 'scanning.html',
              'exploitation': 'exploitation.html'
              }


def open_help(chapter=''):
    """Opens the help in user's preferred browser.

    :param chapter: the chapter of the help, optional.
    """
    try:
        current_branch = get_current_branch()
    except git.exc.InvalidGitRepositoryError:
        current_branch = 'latest'
    else:
        if current_branch in (DETACHED_HEAD, 'master'):
            current_branch = 'latest'

    help_url = DOC_ROOT_FMT % current_branch

    if chapter:
        help_url += DOC_ROUTER.get(chapter.lower(), '')

    webbrowser.open(help_url)