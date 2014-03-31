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
import subprocess
import sys

from w3af.core.controllers.dependency_check.requirements import PIP_PACKAGES
from w3af.core.controllers.dependency_check.pip_dependency import PIPDependency

SYSTEM_NAME = 'Mac OS X'

PKG_MANAGER_CMD = 'sudo port install'

#
#    Remember to use http://www.macports.org/ports.php to search for packages
#
SYSTEM_PACKAGES = {
                   'PIP': ['py27-pip'],
                   # Python port includes the dev headers
                   'C_BUILD': ['python27', 'py27-setuptools',
                                'gcc48', 'autoconf', 'automake'],
                   'GIT': ['git-core'],
                   'SCAPY': ['py27-pcapy', 'py27-libdnet'],
                  }
PIP_CMD = 'pip-2.7' 

# pybloomfilter is broken in Mac OS X, so we don't require it
# https://github.com/andresriancho/w3af/issues/485
PIP_PACKAGES.remove(PIPDependency('pybloomfilter', 'pybloomfiltermmap', '0.3.11'))


def os_package_is_installed(package_name):
    not_installed = 'None of the specified ports are installed'
    installed = 'The following ports are currently installed'
    
    try:
        p = subprocess.Popen(['port', '-v', 'installed', package_name],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except OSError:
        # We're not on a debian based system
        return None
    else:
        port_output = p.stdout.read()

        if not_installed in port_output:
            return False
        elif installed in port_output:
            return True
        else:
            return None


def after_hook():
    # Is the default python executable the one in macports?
    #
    # We need to warn the user about this situation and let him know how to fix
    # See: http://stackoverflow.com/questions/118813/
    msg = '\nIt seems that your system has two different python installations:'\
          ' One provided by the operating system, at %s, and another which'\
          ' you installed using Mac ports. '\
          'The default python executable for your system is the one provided'\
          ' by Apple, and pip-2.7 will install all new libraries in the Mac'\
          ' ports Python.\n\n'\
          'In order to have a working w3af installation you will have to'\
          ' switch to the Mac ports Python by using the following command:\n'\
          '    sudo port select python python27\n'

    if sys.executable.startswith('/opt/'):
        # That's what we need since pip-2.7 will install all the libs in
        # that python site-packages directory
        pass
    else:
        print msg % sys.executable

    #check if scapy is correctly installed/working on OSX
    try:
        from scapy.all import traceroute
    except ImportError:
        # The user just needs to work on his dependencies.
        pass
    except OSError, ose:
        if "Device not configured" in str(ose):
            print('Tried to import traceroute from scapy.all and found an'
                  ' OSError including the message "Device not configured".'
                  ' This is a bug in the scapy library and happens on OSX with'
                  ' MacPorts i.e. when Virtualbox is installed.\n\n'
                  'Please apply the following fix (example for python 2.7):\n'
                  '    - Open the file /opt/local/Library/Frameworks/Python'
                  '.framework/Versions/2.7/lib/python2.7/site-packages/scapy/'
                  'arch/unix.py\n'
                  '    - Change line 34 to read:\n'
                  '        f=os.popen("netstat -rn|grep -v vboxnet") # -f inet\n\n'
                  'Original bug report: '
                  'http://bb.secdev.org/scapy/issue/418/scapy-error-in-mac-osx-leopard')
