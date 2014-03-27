"""
os_detection.py

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
import platform


curr_platform = platform.system().lower()
distro = platform.dist()


def is_mac():
    return 'darwin' in curr_platform or 'mac' in curr_platform


def is_linux():
    return 'linux' in curr_platform


def is_fedora():
    return 'fedora' in distro[0]


def is_centos():
    return 'redhat' in distro[0]


def is_suse():
    return 'SuSE' in distro[0]


def is_openbsd():
    return 'openbsd' in curr_platform


def is_kali():
    return 'debian' in distro and 'kali' in platform.release()