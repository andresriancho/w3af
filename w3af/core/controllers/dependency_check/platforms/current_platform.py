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
from .ubuntu1204 import Ubuntu1204
from .ubuntu1404 import Ubuntu1404
from .debian import Debian
from .centos import CentOS
from .centos65 import CentOS65
from .fedora import Fedora
from .kali import Kali
from .mac import MacOSX
from .openbsd import OpenBSD5
from .suse import SuSE
from .default import DefaultPlatform

KNOWN_PLATFORMS = [Debian, Ubuntu1204, CentOS65, CentOS, Fedora, Kali, MacOSX, OpenBSD5,
                   SuSE, Ubuntu1404]


def get_current_platform(known_platforms=KNOWN_PLATFORMS):
    for known_platform in known_platforms:
        if known_platform.is_current_platform():
            return known_platform()
    else:
        return DefaultPlatform()



