"""
dependency_check.py

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
import sys

from w3af.core.controllers.dependency_check.dependency_check import dependency_check as mdep_check
from .platforms.current_platform import (SYSTEM_NAME,
                                         PKG_MANAGER_CMD,
                                         SYSTEM_PACKAGES,
                                         PIP_CMD,
                                         PIP_PACKAGES)


def dependency_check():
    """
    This dependency check function uses the information stored in the platforms
    module to call the function in core.controllers.dependency_check which
    actually checks for the dependencies.
    
    The data in the core.ui.gui.dependency_check.platforms module is actually
    based on the data stored in core.controllers.dependency_check.platforms,
    we extend() the lists present in the base module before passing them to
    mdep_check() 
    """
    should_exit = mdep_check(pip_packages=PIP_PACKAGES,
                             system_packages=SYSTEM_PACKAGES,
                             system_name=SYSTEM_NAME,
                             pkg_manager_cmd=PKG_MANAGER_CMD,
                             pip_cmd=PIP_CMD, exit_on_failure=False)
    
    try:
        import pygtk
        pygtk.require('2.0')
        import gtk
        import gobject
        assert gtk.gtk_version >= (2, 12)
        assert gtk.pygtk_version >= (2, 12)
    except:
        msg = 'The GTK package requirements are not met, please make sure your'\
              ' system meets these requirements:\n'\
              '    - PyGTK >= 2.12\n'\
              '    - GTK >= 2.12\n'
        print msg
        should_exit = True
    
    if should_exit:
        sys.exit(1)