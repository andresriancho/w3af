'''
fedora.py

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

SYSTEM_NAME = 'fedora'

PKG_MANAGER_CMD = 'sudo yum install'

SYSTEM_PACKAGES = {
                   'PIP': ['python-pip'],
                   'C_BUILD': ['python-devel', 'python-setuptools',
                               'libsqlite3x-devel'],
                   'GIT': ['git'],
                   'XML': ['libxml2-devel', 'libxslt-devel']
                  }
PIP_CMD = 'python-pip'

PHPLY_GIT = 'git+git://github.com/ramen/phply.git#egg=phply'

PIP_PACKAGES = [PIPDependency('clamd', 'clamd'),
                PIPDependency('github', 'PyGithub'),
                PIPDependency('git.util', 'GitPython', SYSTEM_PACKAGES['GIT']),
                PIPDependency('pybloomfilter', 'pybloomfiltermmap',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('esmre', 'esmre'),
                PIPDependency('phply', PHPLY_GIT, is_git=True),
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
                PIPDependency('six', 'six'),
                PIPDependency('msgpack', 'msgpack-python',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('ntlm', 'python-ntlm'),]

def os_package_is_installed(package_name):
    not_installed = 'is not installed'
    installed = 'Status: install ok installed'
    
    try:
        p = subprocess.Popen(['rpm', '-q', package_name], stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
    except OSError:
        # We're not on a debian based system
        return None
    else:
        dpkg_output = p.stdout.read()

        if not_installed in dpkg_output:
            return False
        elif package_name in dpkg_output:
            return True
        else:
            return None

def after_hook():
    pass