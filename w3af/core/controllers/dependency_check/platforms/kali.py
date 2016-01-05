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
import platform

from .ubuntu1204 import Ubuntu1204

KALI_MESSAGE = '''
According to Kali's documentation [0] in order to avoid breaking the packaged\
 w3af version you should run the following commands:

cd ~
apt-get install -y python-pip
pip install --upgrade pip
git clone https/github.com/andresriancho/w3af.git
cd w3af
./w3af_console
. /tmp/w3af_dependency_install.sh

[0] http://www.kali.org/kali-monday/bleeding-edge-kali-repositories/
'''


class Kali(Ubuntu1204):
    SYSTEM_NAME = 'Kali'

    @staticmethod
    def after_hook():
        print(KALI_MESSAGE)

    @staticmethod
    def is_current_platform():
        return 'debian' in platform.dist() and 'kali' in platform.release()

