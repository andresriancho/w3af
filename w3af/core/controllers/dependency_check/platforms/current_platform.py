"""
current_platform.py

Copyright 2013 Andres Riancho

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
from .ubuntu import Ubuntu1204
from .centos import CentOS
from .fedora import Fedora
from .kali import Kali
from .mac import MacOSX
from .openbsd import OpenBSD5
from .suse import SuSE
from .default import DefaultPlatform

KNOWN_PLATFORMS = [Ubuntu1204, CentOS, Fedora, Kali, MacOSX, OpenBSD5, SuSE]


def get_current_platform():
    for known_platform in KNOWN_PLATFORMS:
        if known_platform.is_current_platform():
            return known_platform()
    else:
        return DefaultPlatform()



