'''
homeDir.py

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

'''
import user
import os
import shutil

HOME_DIR = os.path.join(user.home, '.w3af')
W3AF_LOCAL_PATH = os.sep.join(__file__.split(os.sep)[:-4])


def create_home_dir():
    '''
    Creates the w3af home directory, on linux: /home/user/.w3af/
    :return: True if success.
    '''
    # Create .w3af inside home directory
    home_path = get_home_dir()
    if not os.path.exists(home_path):
        try:
            os.makedirs(home_path)
        except OSError:
            return False

    # webroot for some plugins
    webroot = home_path + os.path.sep + 'webroot'
    if not os.path.exists(webroot):
        try:
            os.makedirs(webroot)
        except OSError:
            return False

    # and the profile directory
    home_profiles = home_path + os.path.sep + 'profiles'
    default_profiles = 'profiles' + os.path.sep
    if not os.path.exists(home_profiles):
        try:
            shutil.copytree(default_profiles, home_profiles)
        except OSError:
            return False

    return True


def get_home_dir():
    '''
    :return: The location of the w3af directory inside the home directory of
        the current user.
    '''
    return HOME_DIR


def verify_dir_has_perm(path, perm, levels=0):
    '''
    Verify that home directory has `perm` access for current user. If at
    least one of them fails to have it the result will be False.

    :param path: Path to test
    :param perm: Access rights. Possible values are os' R_OK, W_OK and X_OK or
        the result of a bitwise "|" operator applied a combination of them.
    :param levels: Depth levels to test
    '''
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
        if not all(map(lambda p: os.access(p, perm),
                       (os.path.join(root, f) for f in dirs + files))):
            return False
    return True
