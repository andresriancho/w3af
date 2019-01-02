"""
centos65.py

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

from .centos import CentOS
from ..requirements import CORE, GUI


class CentOS65(CentOS):
    SYSTEM_NAME = 'CentOS 6.5'

    CORE_SYSTEM_PACKAGES = ['python-pip','npm', 'python-devel', 'python-setuptools',
                            'sqlite-devel', 'gcc-c++', 'gcc', 'make', 'git',
                            'libxml2-devel', 'libxslt-devel', 'pyOpenSSL',
                            'openssl-devel', 'libcom_err-devel', 'libcom_err']

    GUI_SYSTEM_PACKAGES = CORE_SYSTEM_PACKAGES[:]
    GUI_SYSTEM_PACKAGES.extend(['graphviz', 'gtksourceview2', 'pygtksourceview',
                                'pywebkitgtk'])

    SYSTEM_PACKAGES = {CORE: CORE_SYSTEM_PACKAGES,
                       GUI: GUI_SYSTEM_PACKAGES}

    @staticmethod
    def is_current_platform():
        return 'centos' in platform.dist() and '6.5' in platform.dist()
