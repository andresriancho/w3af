"""
linux.py

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

SYSTEM_NAME = 'Debian'

PKG_MANAGER_CMD = 'sudo apt-get install'

SYSTEM_PACKAGES = {
                   'PIP': ['python-pip'],
                   'C_BUILD': ['python2.7-dev', 'python-setuptools',
                               'build-essential', 'libsqlite3-dev'],
                   'SSL_DEV': ['libssl-dev',],
                   'GIT': ['git'],
                   'XML': ['libxml2-dev', 'libxslt1-dev'],
                   'YAML': ['libyaml-dev']
                  }
PIP_CMD = 'pip'


def os_package_is_installed(package_name):
    not_installed = 'is not installed and no info is available'
    installed = 'Status: install ok installed'
    
    try:
        p = subprocess.Popen(['dpkg', '-s', package_name], stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
    except OSError:
        # We're not on a debian based system
        return None
    else:
        dpkg_output = p.stdout.read()

        if not_installed in dpkg_output:
            return False
        elif installed in dpkg_output:
            return True
        else:
            return None

def after_hook():
    pass
