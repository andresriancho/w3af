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
from w3af.core.controllers.dependency_check.os_detection import (is_mac,
                                                                 is_openbsd,
                                                                 is_fedora,
                                                                 is_suse,
                                                                 is_centos,
                                                                 is_kali)
from w3af.core.ui.gui.dependency_check.requirements import PIP_PACKAGES


if is_mac():
    from .mac import (SYSTEM_NAME, PKG_MANAGER_CMD,
                      SYSTEM_PACKAGES, PIP_CMD,
                      os_package_is_installed,
                      after_hook)

elif is_openbsd():
    from .openbsd import (SYSTEM_NAME, PKG_MANAGER_CMD,
                          SYSTEM_PACKAGES, PIP_CMD,
                          os_package_is_installed,
                          after_hook)

elif is_fedora():
    from .fedora import (SYSTEM_NAME, PKG_MANAGER_CMD,
                         SYSTEM_PACKAGES, PIP_CMD,
                         os_package_is_installed,
                         after_hook)

elif is_centos():
    from .centos import (SYSTEM_NAME, PKG_MANAGER_CMD,
                         SYSTEM_PACKAGES, PIP_CMD,
                         os_package_is_installed,
                         after_hook)

elif is_suse():
    from .suse import (SYSTEM_NAME, PKG_MANAGER_CMD,
                       SYSTEM_PACKAGES, PIP_CMD,
                       os_package_is_installed,
                       after_hook)

elif is_kali():
    from .kali import (SYSTEM_NAME, PKG_MANAGER_CMD,
                       SYSTEM_PACKAGES, PIP_CMD,
                       os_package_is_installed,
                       after_hook)

else:
    from .linux import (SYSTEM_NAME, PKG_MANAGER_CMD,
                        SYSTEM_PACKAGES, PIP_CMD,
                        os_package_is_installed,
                        after_hook)
