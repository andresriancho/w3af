'''
openbsd.py

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

SYSTEM_NAME = 'OpenBSD 5.1'

PKG_MANAGER_CMD = 'pkg_add -v'

#
#    Package list here http://ftp.openbsd.org/pub/OpenBSD/5.1/packages/i386/
#
SYSTEM_PACKAGES = {
                   'PIP': ['py-pip'],
                   'C_BUILD': ['python2.7', 'py-setuptools', 'gcc-4.6.2'],
                   'GIT': ['git'],
                   'XML': ['libxml', 'libxslt']
                  }
PIP_CMD = 'pip'

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
                PIPDependency('lxml', 'lxml', SYSTEM_PACKAGES['XML']),
                PIPDependency('scapy.config', 'scapy-real'),
                PIPDependency('guess_language', 'guess-language'),
                PIPDependency('cluster', 'cluster'),
                PIPDependency('msgpack', 'msgpack-python',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('ntlm', 'python-ntlm'),]

def os_package_is_installed(package_name):
    # TODO: Improve this function, it should also check for the negative case
    # just like the one in linux.py (see not_installed)
    installed = 'Information for '
    
    try:
        p = subprocess.Popen(['pkg_info', package_name], stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE)
    except OSError:
        # We're not on an openbsd based system
        return None
    else:
        pkg_info_output = p.stdout.read()

        if installed in pkg_info_output:
            return True
        else:
            return False