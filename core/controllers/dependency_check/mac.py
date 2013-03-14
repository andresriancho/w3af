'''
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

'''
import subprocess

from core.controllers.dependency_check.pip_dependency import PIPDependency

SYSTEM_NAME = 'Mac OSX'

PKG_MANAGER_CMD = 'sudo port install'

#
#    Remember to use http://www.macports.org/ports.php to search for packages
#
SYSTEM_PACKAGES = {
                   'PIP': ['py27-pip'],
                   # Python port includes the dev headers
                   'C_BUILD': ['python27', 'py27-distribute',
                                'gcc48', 'autoconf', 'automake'],
                   'GIT': ['git-core'],
                  }
PIP_CMD = 'pip-2.7' 

PIP_PACKAGES = [PIPDependency('github', 'PyGithub'),
                PIPDependency('git', 'GitPython', SYSTEM_PACKAGES['GIT']),
                PIPDependency('pybloomfilter', 'pybloomfiltermmap',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('esmre', 'esmre'),
                PIPDependency('sqlite3', 'pysqlite'),
                PIPDependency('nltk', 'nltk'),
                PIPDependency('chardet', 'chardet'),
                PIPDependency('pdfminer', 'pdfminer'),
                PIPDependency('concurrent.futures', 'futures'),
                PIPDependency('OpenSSL', 'pyOpenSSL'),
                # http://lxml.de/installation.html
                PIPDependency('lxml', 'lxml'),
                PIPDependency('scapy.config', 'scapy-real'),
                PIPDependency('guess_language', 'guess-language'),
                PIPDependency('cluster', 'cluster'),
                PIPDependency('msgpack', 'msgpack-python',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('ntlm', 'python-ntlm'),]

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