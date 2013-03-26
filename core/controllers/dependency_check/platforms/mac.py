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
import sys

from core.controllers.dependency_check.pip_dependency import PIPDependency

SYSTEM_NAME = 'Mac OS X'

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
                   'SCAPY': ['py27-libdnet'],
                  }
PIP_CMD = 'pip-2.7' 

PIP_PACKAGES = [PIPDependency('github', 'PyGithub'),
                PIPDependency('git', 'GitPython', SYSTEM_PACKAGES['GIT']),
                PIPDependency('pybloomfilter', 'pybloomfiltermmap',
                              SYSTEM_PACKAGES['C_BUILD']),
                PIPDependency('esmre', 'esmre'),
                PIPDependency('phply', 'phply'),
                PIPDependency('sqlite3', 'pysqlite'),
                PIPDependency('nltk', 'nltk'),
                PIPDependency('chardet', 'chardet'),
                PIPDependency('pdfminer', 'pdfminer'),
                PIPDependency('concurrent.futures', 'futures'),
                PIPDependency('OpenSSL', 'pyOpenSSL'),
                # http://lxml.de/installation.html
                PIPDependency('lxml', 'lxml'),
                PIPDependency('scapy.config', 'scapy-real', SYSTEM_PACKAGES['SCAPY']),
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

def after_hook():
    # Is the default python executable the one in macports?
    if sys.executable.startswith('/opt/'):
        # That's what we need since pip-2.7 will install all the libs in
        # that python site-packages directory
        return
    
    # We need to warn the user about this situation and let him know how to fix
    # See: http://stackoverflow.com/questions/118813/
    msg = 'It seems that your system has two different python installations:'\
          ' One provided by the operating system, at %s, and another which'\
          ' you installed using Mac ports.\n\n'\
          'The default python executable for your system is the one provided'\
          ' by Apple, and pip-2.7 will install all new libraries in the Mac'\
          ' ports Python.\n\n'\
          'In order to have a working w3af installation you will have to'\
          ' switch to the Mac ports Python by using the following command:\n'\
          '    sudo port select python python27\n\n'
    print msg % sys.executable