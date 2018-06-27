"""
chrome.py

Copyright 2018 Andres Riancho

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
import subprocess

from w3af.core.controllers.misc.which import which


def chrome_is_installed():
    """
    :return: True if Google Chrome is installed and we were able to parse the version.
    """
    chrome_path = get_chrome_path()
    if chrome_path is not None:
        return True

    return False


def get_chrome_path():
    paths_to_chrome = []
    paths_to_chrome.extend(which('google-chrome'))
    paths_to_chrome.extend(which('google-chrome-stable'))

    if not paths_to_chrome:
        return False

    for path_to_chrome in paths_to_chrome:

        version = subprocess.check_output('%s --version' % path_to_chrome, shell=True)
        version = version.strip()

        # Google Chrome 67.0.3396.99
        if 'Google Chrome' in version:
            return paths_to_chrome

    return None
