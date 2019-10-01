"""
temp_dir.py

Copyright 2009 Andres Riancho

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
import stat
import errno
import shutil

from w3af.core.controllers.misc.home_dir import get_home_dir

TEMP_DIR = os.path.join(get_home_dir(), 'tmp', str(os.getpid()))


def get_temp_dir():
    """
    :return: The path where we should create the dir.
    """
    return TEMP_DIR


def create_temp_dir():
    """
    Create the temp directory for w3af to work inside.

    :return: A string that contains the temp directory to use,
             in Linux: "~/.w3af/tmp/<pid>"
    """
    complete_dir = get_temp_dir()
    if not os.path.exists(complete_dir):
        try:
            os.makedirs(complete_dir)
        except OSError, ose:
            # I don't care if someone already created it in a different thread,
            # but if we have any other exception, we raise!
            if ose.errno != errno.EEXIST:
                raise

        os.chmod(complete_dir, stat.S_IRWXU)
    return complete_dir


def remove_temp_dir(ignore_errors=False):
    """
    Remove the temp directory.
    """
    shutil.rmtree(get_temp_dir(), ignore_errors=ignore_errors)

