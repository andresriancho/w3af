'''
dependency_check.py

Copyright 2006 Andres Riancho

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
import sys
import platform
import warnings
import subprocess

from core.controllers.dependency_check.lazy_load import lazy_load


PYTHON_PIP = 'python-pip'
PIP_INSTALL = 'http://www.pip-installer.org/en/latest/installing.html'

C_BUILD_PACKAGES = ['python2.7-dev', 'python-setuptools', 'build-essential']

class PIPDependency(object):
    def __init__(self, module_name, package_name, os_packages=[]):
        self.module_name = module_name
        self.package_name = package_name
        self.os_packages = [PYTHON_PIP,]
        self.os_packages.extend(os_packages)

PIP_PACKAGES = [PIPDependency('github', 'PyGithub'),
                PIPDependency('git', 'GitPython', ['git']),
                PIPDependency('pybloomfilter', 'pybloomfiltermmap', C_BUILD_PACKAGES),
                PIPDependency('esmre', 'esmre'),
                PIPDependency('sqlite3', 'pysqlite'),
                PIPDependency('nltk', 'nltk'),
                PIPDependency('chardet', 'chardet'),
                PIPDependency('pdfminer', 'pdfminer'),
                PIPDependency('concurrent.futures', 'futures'),
                PIPDependency('OpenSSL', 'pyOpenSSL'),
                PIPDependency('lxml', 'lxml', ['libxml2-dev', 'libxslt-dev']),
                PIPDependency('scapy.config', 'scapy-real'),
                PIPDependency('guess_language', 'guess-language'),
                PIPDependency('cluster', 'cluster'),
                PIPDependency('msgpack', 'msgpack-python', C_BUILD_PACKAGES),
                PIPDependency('ntlm', 'python-ntlm'),]

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
    
    
def verify_python_version():
    '''
    Check python version eq 2.6 or 2.7
    '''
    major, minor, micro, releaselevel, serial = sys.version_info
    if major == 2:
        if minor not in (6, 7):
            msg = 'Error: Python 2.%s found but Python 2.6 or 2.7 required.' % minor
            print msg
    elif major > 2:
        msg = 'It seems that you are running Python 3k, please let us know if' \
              ' w3af works as expected at w3af-develop@lists.sourceforge.net !'
        print msg
        sys.exit(1)

def pip_installed():
    try:
        return not bool(subprocess.call(['pip', 'help'], stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE))
    except OSError:
        return False
        
    
def dependency_check():
    '''
    This function verifies that the dependencies that are needed by the
    framework core are met.
    '''
    verify_python_version()
    
    # nltk raises a warning... which I want to ignore...
    warnings.filterwarnings('ignore', '.*',)

    failed_deps = []
    for w3af_dependency in PIP_PACKAGES:
        try:
            if not lazy_load(w3af_dependency.module_name):
                failed_deps.append(w3af_dependency)
        except KeyboardInterrupt:
            print 'User exit with Ctrl+C.'
            sys.exit(-1)
    
    if not failed_deps:
        return

    #
    #    Report all missing python modules
    #    
    msg = 'Your python installation needs the following modules'\
          ' to run w3af:\n'
    msg += '    ' + ' '.join([fdep.module_name for fdep in failed_deps])
    print msg, '\n'
    
    #
    #    Report all missing operating system packages
    #
    curr_platform = platform.system().lower()
    
    os_packages = []
    for fdep in failed_deps:
        os_packages.extend(fdep.os_packages)
    os_packages = list(set(os_packages))
    
    if pip_installed():
        os_packages.remove(PYTHON_PIP)
    
    os_packages = [pkg for pkg in os_packages if not os_package_is_installed(pkg)]
    
    if os_packages and 'linux' in curr_platform:
        msg = 'On Debian based systems please install the following operating'\
              ' system packages before running the pip installer:\n'
        msg += '    sudo apt-get install ' + ' '.join(os_packages)
        print msg, '\n'
    
    #
    #    Report missing pip packages
    #
    packages_pip = [fdep.package_name for fdep in failed_deps]
    
    msg = 'After installing any missing operating system packages, use pip to'\
          ' install the remaining modules:\n'
    msg += '    sudo pip install ' + ' '.join(packages_pip)
    print msg, '\n'

    sys.exit(1)


def mem_test(when):
    from core.controllers.profiling.ps_mem import get_memory_usage, human
    sorted_cmds, shareds, _, _ = get_memory_usage(None, True, True, True)
    cmd = sorted_cmds[0]
    msg = "%8sB Private + %8sB Shared = %8sB" % (human(cmd[1] - shareds[cmd[0]]),
                                                 human(shareds[cmd[
                                                               0]]), human(cmd[1])
                                                 )
    print 'Total memory usage %s: %s' % (when, msg)


def is_mac(curr_platform):
    return 'darwin' in curr_platform or 'mac' in curr_platform
