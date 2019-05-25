"""
suse.py

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


class SuSE(Platform):
    SYSTEM_NAME = 'SuSE'
    PKG_MANAGER_CMD = 'sudo zypper install'
    PIP_CMD = 'pip-2.7'

    CORE_SYSTEM_PACKAGES = ['python-pip','npm', 'python-devel', 'sqlite3-devel',
                            'git', 'libxml2-devel', 'libxslt-devel',
                            'python-webkitgtk', 'libffi-devel']

    GUI_SYSTEM_PACKAGES = CORE_SYSTEM_PACKAGES[:]
    GUI_SYSTEM_PACKAGES.extend(['graphviz', 'python-gtksourceview',
                                'python-gtk', 'python-webkitgtk'])

    SYSTEM_PACKAGES = {CORE: CORE_SYSTEM_PACKAGES,
                       GUI: GUI_SYSTEM_PACKAGES}

    @staticmethod
    def os_package_is_installed(package_name):
        not_installed = 'is not installed'
        installed = 'Status: install ok installed'

        try:
            p = subprocess.Popen(['rpm', '-q', package_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            # We're not on a suse based system
            return None
        else:
            rpm_output, _ = p.communicate()

            if not_installed in rpm_output:
                return False
            elif package_name in rpm_output:
                return True
            else:
                return None

    @staticmethod
    def is_current_platform():
        return 'SuSE' in platform.dist()[0]
