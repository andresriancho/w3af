"""
mac.py

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
import platform
import subprocess

from w3af.core.controllers.dependency_check.pip_dependency import PIPDependency
from w3af.core.controllers.dependency_check.platforms.base_platform import Platform
from w3af.core.controllers.dependency_check.requirements import CORE_PIP_PACKAGES, GUI_PIP_EXTRAS, CORE, GUI


TWO_PYTHON_MSG = """\
It seems that your system has two different python installations: One provided
by the operating system, at %s, and another which you installed using Mac ports.

The default python executable for your system is the one provided by Apple,
and pip-2.7 will install all new libraries in the Mac ports Python.

In order to have a working w3af installation you will have to switch to the Mac
ports Python by using the following command:
    sudo port select python python27
"""

TRACEROUTE_SCAPY_MSG = """\
Tried to import traceroute from scapy.all and found an OSError including the
message "Device not configured".
"""


class MacOSX(Platform):
    SYSTEM_NAME = 'Mac OS X'
    PKG_MANAGER_CMD = 'sudo port install'
    PIP_CMD = 'pip-2.7'

    #
    # Remember to use http://www.macports.org/ports.php to search for
    # packages
    #
    # Python port includes the dev headers
    CORE_SYSTEM_PACKAGES = ['py27-pip', 'python27', 'py27-setuptools', 'gcc48',
                            'autoconf', 'automake', 'git-core', 'py27-pcapy',
                            'py27-libdnet', 'libffi']

    GUI_SYSTEM_PACKAGES = CORE_SYSTEM_PACKAGES[:]
    GUI_SYSTEM_PACKAGES.extend(['graphviz', 'py27-pygtksourceview',
                                'py27-pygtk', 'py27-webkitgtk'])

    SYSTEM_PACKAGES = {CORE: CORE_SYSTEM_PACKAGES,
                       GUI: GUI_SYSTEM_PACKAGES}

    # pybloomfilter is broken in Mac OS X, so we don't require it
    # https://github.com/andresriancho/w3af/issues/485
    MAC_CORE_PIP_PACKAGES = CORE_PIP_PACKAGES[:]
    MAC_CORE_PIP_PACKAGES.remove(PIPDependency('pybloomfilter',
                                               'pybloomfiltermmap', '0.3.14'))

    MAC_GUI_PIP_PACKAGES = MAC_CORE_PIP_PACKAGES[:]
    MAC_GUI_PIP_PACKAGES.extend(GUI_PIP_EXTRAS)

    PIP_PACKAGES = {CORE: MAC_CORE_PIP_PACKAGES,
                    GUI: MAC_GUI_PIP_PACKAGES}

    @staticmethod
    def is_current_platform():
        return 'darwin' in platform.dist() or 'mac' in platform.dist()

    @staticmethod
    def os_package_is_installed(package_name):
        not_installed = 'None of the specified ports are installed'
        installed = 'The following ports are currently installed'

        try:
            p = subprocess.Popen(['port', '-v', 'installed', package_name],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except OSError:
            # We're not on a mac based system
            return None
        else:
            port_output, _ = p.communicate()

            if not_installed in port_output:
                return False
            elif installed in port_output:
                return True
            else:
                return None

    @staticmethod
    def after_hook():
        # Is the default python executable the one in macports?
        #
        # We need to warn the user about this situation and let him know how to
        # fix. See: http://stackoverflow.com/questions/118813/
        if sys.executable.startswith('/opt/'):
            # That's what we need since pip-2.7 will install all the libs in
            # that python site-packages directory
            pass
        else:
            print TWO_PYTHON_MSG % sys.executable

        #check if scapy is correctly installed/working on OSX
        try:
            from scapy.all import traceroute
        except ImportError:
            # The user just needs to work on his dependencies.
            pass
        except OSError, ose:
            if "Device not configured" in str(ose):
                print(TRACEROUTE_SCAPY_MSG)
