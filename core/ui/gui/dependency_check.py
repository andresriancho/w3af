'''
dependency_check.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import platform
import subprocess

import core.controllers.output_manager as om

from core.controllers.dependency_check.dependency_check import is_mac


def gtkui_dependency_check():
    '''
    This function verifies that the dependencies that are needed by the GTK
    user interface are met.
    '''
    reason_for_exit = False
    packages = []
    packages_debian = []
    packages_mac_ports = []
    packages_pip = []
    packages_openbsd = []
    additional_information = []

    om.out.debug('Checking GTK UI dependencies')

    try:
        proc = subprocess.Popen('neato -V', shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except:
        packages_debian.append('graphviz')
        packages_mac_ports.append('graphviz')
        packages_openbsd.append('graphviz')
        reason_for_exit = True
    else:
        
        # E1101: Instance of 'Popen' has no 'stderr' member
        if 'graphviz' not in proc.stderr.read().lower(): # pylint: disable=E1101
            packages_debian.append('graphviz')
            packages_mac_ports.append('graphviz')
            reason_for_exit = True
        

    try:
        import pygtk
        pygtk.require('2.0')
        import gtk
        import gobject
        assert gtk.gtk_version >= (2, 12)
        assert gtk.pygtk_version >= (2, 12)
    except:
        packages.extend(['pygtk', 'gtk'])
        packages_debian.append('python-gtk2')
        packages_mac_ports.append('py26-gtk')
        reason_for_exit = True

    try:
        import xdot
    except ImportError:
        packages_pip.append('xdot')
        reason_for_exit = True

    try:
        import gtksourceview2
    except:
        packages.append('gtksourceview2')
        packages_debian.append('python-gtksourceview2')
        packages_openbsd.append('gtksourceview')
        reason_for_exit = True

    curr_platform = platform.system().lower()

    if packages:
        msg = 'Your python installation needs the following packages:\n'
        msg += '    ' + ' '.join(packages)
        print msg, '\n'
    if packages_debian and 'linux' in curr_platform:
        msg = 'On debian based systems:\n'
        msg += '    sudo apt-get install ' + ' '.join(packages_debian)
        print msg, '\n'
    if packages_mac_ports and is_mac(curr_platform):
        msg = 'On a mac with mac ports installed:\n'
        msg += '    sudo port install ' + ' '.join(packages_mac_ports)
        print msg, '\n'
    if packages_openbsd and 'openbsd' in curr_platform:
        msg = 'On a OpenBSD 5.1 install the requirements by running:\n'
        msg += '    export PKG_PATH="http://ftp.openbsd.org/pub/OpenBSD/5.1/packages/i386/"\n'
        msg += '    pkg_add -v  ' + ' '.join(packages_openbsd)
        print msg, '\n'
    if packages_pip:
        msg = 'After installing any missing operating system packages, use'\
              ' pip to install the remaining modules:\n'
        msg += '    sudo pip install ' + ' '.join(packages_pip)
        print msg, '\n'
    if additional_information:
        msg = 'Additional information:\n'
        msg += '\n'.join(additional_information)
        print msg

    #Now exit if necessary
    if reason_for_exit:
        exit(1)
