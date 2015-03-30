"""
default.py

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
from .base_platform import Platform
from ..requirements import CORE, GUI


class DefaultPlatform(Platform):
    PIP_CMD = 'pip'

    # Should never be used since we have an empty SYSTEM_PACKAGES
    PKG_MANAGER_CMD = ''

    SYSTEM_PACKAGES = {CORE: [],
                       GUI: []}

    @staticmethod
    def is_current_platform():
        return True

    @staticmethod
    def os_package_is_installed(package_name):
        return False