"""
home_dir.py

Copyright 2008 Andres Riancho

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
import sys
import shutil

from w3af import ROOT_PATH

HOME_DIR = os.path.join(os.path.expanduser('~'), '.w3af')

# Point to the directory where w3af_console , w3af_gui and profiles/ live
# Also, the root of the git repository
W3AF_LOCAL_PATH = os.sep.join(__file__.split(os.sep)[:-5]) + os.path.sep


def create_home_dir():
    """
    Creates the w3af home directory, on linux: /home/user/.w3af/
    :return: True if success.
    """
    # Create .w3af inside home directory
    home_path = get_home_dir()
    if not os.path.exists(home_path):
        try:
            os.makedirs(home_path)
        except OSError:
            # Handle some really strange cases where there is a race-condition
            # where multiple w3af processes are starting and creating the same
            # directory
            #
            # https://circleci.com/gh/andresriancho/w3af/1347
            if not os.path.exists(home_path):
                return False

    # webroot for some plugins
    webroot = os.path.join(home_path, 'webroot')
    if not os.path.exists(webroot):
        try:
            os.makedirs(webroot)
        except OSError:
            # Handle some really strange cases where there is a race-condition
            # where multiple w3af processes are starting and creating the same
            # directory
            #
            # https://circleci.com/gh/andresriancho/w3af/1347
            if not os.path.exists(webroot):
                return False

    # and the profile directory
    home_profiles = os.path.join(home_path, 'profiles')

    # I need to check in two different paths to support installing w3af as
    # a module. Note the gen_data_files.py code in the w3af-module.
    default_profiles_paths = [os.path.join(W3AF_LOCAL_PATH, 'profiles'),
                              os.path.join(ROOT_PATH, 'profiles'),
                              os.path.join(ROOT_PATH, '../profiles'),
                              os.path.join(sys.prefix, 'profiles'),
                              os.path.join(sys.exec_prefix, 'profiles'),
                              # https://github.com/andresriancho/w3af-module/issues/4
                              os.path.join(sys.prefix, 'local', 'profiles'),
                              os.path.join(sys.exec_prefix, 'local', 'profiles')]

    if not os.path.exists(home_profiles):
        for default_profile_path in default_profiles_paths:
            if not os.path.exists(default_profile_path):
                continue

            try:
                shutil.copytree(default_profile_path, home_profiles)
            except OSError:
                return False
            else:
                break
        else:
            return False

    return True


def get_home_dir():
    """
    :return: The location of the w3af directory inside the home directory of
        the current user.
    """
    return os.environ.get('W3AF_HOME_DIR', HOME_DIR)


def verify_dir_has_perm(path, perm, levels=0):
    """
    Verify that home directory has `perm` access for current user. If at
    least one of them fails to have it the result will be False.

    :param path: Path to test
    :param perm: Access rights. Possible values are os' R_OK, W_OK and X_OK or
        the result of a bitwise "|" operator applied a combination of them.
    :param levels: Depth levels to test
    """
    if not os.path.exists(path):
        raise RuntimeError('%s does NOT exist!' % path)
    
    path = os.path.normpath(path)
    pdepth = len(path.split(os.path.sep))

    pathaccess = os.access(path, perm)

    # 0th level
    if not levels or not pathaccess:
        return pathaccess

    # From 1st to `levels`th
    for root, dirs, files in os.walk(path):
        currentlevel = len(root.split(os.path.sep)) - pdepth
        
        if currentlevel > levels:
            break
        elif ".git" in dirs:
            dirs.remove(".git")

        for file_path in (os.path.join(root, f) for f in dirs + files):
            if os.path.exists(file_path):
                if not os.access(file_path, perm):
                    #print('No permissions for "%s".' % file_path)
                    return False
    return True

