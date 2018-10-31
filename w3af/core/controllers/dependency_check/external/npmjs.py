"""
retirejs.py

Copyright 2018 CustomBread

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


def npmjs_is_installed():
    """
    :return: True if npmjs is installed and we were able to parse the version.
    """
    paths_to_npm = which('npm')
    if not paths_to_npm:
        return False

    paths_to_npm = paths_to_npm[0]

    try:
        version = subprocess.check_output('%s --version' % paths_to_npm, shell=True)
    except subprocess.CalledProcessError:
        return False

    version = version.strip()
    version_split = version.split('.')

    # Just check that the version has the format 6.4.1
    if len(version_split) != 3:
        return False

    return True
