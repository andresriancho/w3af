'''
temp_dir.py

Copyright 2009 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
import os
import stat
import shutil

from core.controllers.misc.homeDir import get_home_dir

TEMP_DIR = os.path.join(get_home_dir(), 'tmp', str(os.getpid()))

def get_temp_dir():
    '''
    @return: The path where we should create the dir.
    '''
    return TEMP_DIR

def create_temp_dir():
    '''
    Create the temp directory for w3af to work inside.

    @return: A string that contains the temp directory to use, in Linux: "~/.w3af/tmp/<pid>"
    '''
    complete_dir = get_temp_dir()
    if os.path.exists(complete_dir):
        remove_temp_dir()
    os.makedirs(complete_dir)
    os.chmod(complete_dir, stat.S_IRWXU)
    return complete_dir

def remove_temp_dir():
    '''
    Remove the temp directory.
    '''
    shutil.rmtree(get_temp_dir(), ignore_errors=True)
