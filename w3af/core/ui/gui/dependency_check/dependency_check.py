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

from w3af.core.controllers.misc.which import which
from w3af.core.controllers.dependency_check.dependency_check import dependency_check as mdep_check
from w3af.core.controllers.dependency_check.platforms.base_platform import GUI


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
    should_exit = mdep_check(dependency_set=GUI, exit_on_failure=False)

    errors = []

    try:
        import pygtk
    except ImportError:
        errors.append('Failed to import module pygtk')
    else:
        try:
            pygtk.require('2.0')
        except:
            errors.append('Failed to find required pygtk version 2.0')

    try:
        import gtk
    except ImportError:
        errors.append('Failed to import module gtk')
    else:
        try:
            assert gtk.gtk_version >= (2, 12)
        except AssertionError:
            errors.append('Failed to find gtk version 2.12 or greater')

        try:
            assert gtk.pygtk_version >= (2, 12)
        except AssertionError:
            errors.append('Failed to find gtk / pygtk version 2.12 or greater')

    try:
        import gobject
    except ImportError:
        errors.append('Failed to import module gobject')

    #
    # Now print a detailed error message with all the errors (if any)
    #
    if errors:
        msg = ('The GTK user interface package requirements are not met,'
               ' please make sure your system meets these requirements:\n'
               '    - PyGTK >= 2.12\n'
               '    - GTK >= 2.12\n'
               '\n'
               'The following errors were found:\n'
               '%s')
        errors_as_str = ''.join('    - %s\n' % e for e in errors)
        print(msg % errors_as_str)

        should_exit = True

    if not which('dot'):
        msg = ('The required "dot" binary is missing, please install the'
               ' "graphviz" package in your operating system.')
        print(msg)
        should_exit = True

    if should_exit:
        sys.exit(1)
