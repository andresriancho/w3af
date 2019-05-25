"""
ubuntu1204.py

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


class Ubuntu1204(Platform):
    SYSTEM_NAME = 'Ubuntu 12.04'
    PKG_MANAGER_CMD = 'sudo apt-get -y install'
    PIP_CMD = 'pip'

    CORE_SYSTEM_PACKAGES = ['python-pip', 'npm', 'python2.7-dev',
                            'python-setuptools', 'build-essential',
                            'libsqlite3-dev', 'libssl-dev', 'git',
                            'libxml2-dev', 'libxslt1-dev', 'libyaml-dev',
                            'libffi-dev']

    GUI_SYSTEM_PACKAGES = CORE_SYSTEM_PACKAGES[:]
    GUI_SYSTEM_PACKAGES.extend(['graphviz', 'python-gtksourceview2',
                                'python-gtk2', 'python-webkit'])

    SYSTEM_PACKAGES = {CORE: CORE_SYSTEM_PACKAGES,
                       GUI: GUI_SYSTEM_PACKAGES}

    @staticmethod
    def os_package_is_installed(package_name):
        not_installed = 'is not installed and no info is available'

        # The hold string was added after a failed build of w3af-module
        installed = 'Status: install ok installed'
        hold = 'Status: hold ok installed'

        try:
            p = subprocess.Popen(['dpkg', '-s', package_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            # We're not on a debian based system
            return None
        else:
            dpkg_output, _ = p.communicate()

            if not_installed in dpkg_output:
                return False
            elif installed in dpkg_output or hold in dpkg_output:
                return True
            else:
                return None

    @staticmethod
    def is_current_platform():
        return 'Ubuntu' in platform.dist() and '12.04' in platform.dist()
