"""
openbsd.py

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
import subprocess

SYSTEM_NAME = 'OpenBSD 5'

PKG_MANAGER_CMD = 'pkg_add -i -v'

#
#    Package list here http://ftp.openbsd.org/pub/OpenBSD/5.2/packages/i386/
#
SYSTEM_PACKAGES = {
                   'PIP': ['py-pip'],
                   'C_BUILD': ['python-2.7.3p0', 'py-setuptools', 'gcc'],
                   'GIT': ['git'],
                   'XML': ['libxml', 'libxslt'],
                   'SCAPY': ['py-pcapy', 'py-libdnet'],
                  }
PIP_CMD = 'pip-2.7'


def os_package_is_installed(package_name):
    command = 'pkg_info | grep "^%s"' % package_name
    
    try:
        pkg_info_output = subprocess.check_output(command, shell=True)
    except:
        # We're not on an openbsd based system
        return None
    else:
        return pkg_info_output.startswith(package_name)

def after_hook():
    msg = 'Before running pkg_add remember to specify the package path using:\n'\
          '    export PKG_PATH=ftp://ftp.openbsd.org/pub/OpenBSD/`uname'\
          ' -r`/packages/`machine -a`/'
    print msg