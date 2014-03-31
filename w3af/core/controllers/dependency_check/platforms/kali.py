"""
kali.py

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
from .linux import (PKG_MANAGER_CMD, SYSTEM_PACKAGES, PIP_CMD,
                    os_package_is_installed)

#
#   This piece of code will most likely be patched to be ignored when we create
#   the latest deb package for Kali.
#

SYSTEM_NAME = 'Kali'

KALI_MESSAGE = '''
According to Kali's documentation [0] in order to avoid breaking the packaged\
 w3af version you should run the following commands:

cd ~
apt-get install -y python-pip
pip install --upgrade pip
git clone  1 https/github.com/andresriancho/w3af.git
cd w3af
./w3af_console
. /tmp/w3af_dependency_install.sh

[0] http://www.kali.org/kali-monday/bleeding-edge-kali-repositories/
'''


def after_hook():
    print(KALI_MESSAGE)


