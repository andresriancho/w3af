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
import platform
import subprocess

from .base_platform import Platform
from ..requirements import CORE, GUI


class OpenBSD5(Platform):
    SYSTEM_NAME = 'OpenBSD 5'
    PKG_MANAGER_CMD = 'pkg_add -i -v'
    PIP_CMD = 'pip-2.7'

    #
    #    Package list here http://ftp.openbsd.org/pub/OpenBSD/5.2/packages/i386/
    #
    CORE_SYSTEM_PACKAGES = ['py-pip', 'python-2.7.3p0', 'py-setuptools',
                            'gcc', 'git', 'libxml', 'libxslt', 'py-pcapy',
                            'py-libdnet', 'libffi']

    GUI_SYSTEM_PACKAGES = CORE_SYSTEM_PACKAGES[:]
    GUI_SYSTEM_PACKAGES.extend(['graphviz', 'gtksourceview'])

    SYSTEM_PACKAGES = {CORE: CORE_SYSTEM_PACKAGES,
                       GUI: GUI_SYSTEM_PACKAGES}

    @staticmethod
    def os_package_is_installed(package_name):
        command = 'pkg_info | grep "^%s"' % package_name

        try:
            pkg_info_output = subprocess.check_output(command, shell=True)
        except:
            # We're not on an openbsd based system
            return None
        else:
            return pkg_info_output.startswith(package_name)

    @staticmethod
    def after_hook():
        msg = 'Before running pkg_add remember to specify the package path using:\n'\
              '    export PKG_PATH=ftp://ftp.openbsd.org/pub/OpenBSD/`uname'\
              ' -r`/packages/`machine -a`/'
        print msg

    @staticmethod
    def is_current_platform():
        return 'openbsd' in platform.system().lower()