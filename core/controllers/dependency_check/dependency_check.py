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
import warnings

from .lazy_load import lazy_load
from .utils import verify_python_version, pip_installed
from .platforms.current_platform import (SYSTEM_NAME,
                                         PKG_MANAGER_CMD,
                                         SYSTEM_PACKAGES,
                                         PIP_CMD,
                                         PIP_PACKAGES,
                                         os_package_is_installed,
                                         after_hook)

    
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
    os_packages = []
    for fdep in failed_deps:
        os_packages.extend(fdep.os_packages)
    os_packages = list(set(os_packages))
    os_packages = [pkg for pkg in os_packages if not os_package_is_installed(pkg)]

    if not pip_installed():
        os_packages.extend(SYSTEM_PACKAGES['PIP'])
    
    if os_packages:
        missing_pkgs = ' '.join(os_packages)
        
        msg = 'On %s systems please install the following operating'\
              ' system packages before running the pip installer:\n'\
              '    %s %s\n' 
        print msg % (SYSTEM_NAME, PKG_MANAGER_CMD, missing_pkgs)
            
    #
    #    Report missing pip packages
    #
    not_git_pkgs = [fdep.package_name for fdep in failed_deps if not fdep.is_git]
    git_pkgs = [fdep.package_name for fdep in failed_deps if fdep.is_git]
    
    msg = 'After installing any missing operating system packages, use pip to'\
          ' install the remaining modules:\n'
    
    if not_git_pkgs:
        msg += '    sudo %s install %s\n' % (PIP_CMD, ' '.join(not_git_pkgs))
    
    if git_pkgs:
        for missing_git_pkg in git_pkgs:
            msg += '    sudo %s install -e %s\n' % (PIP_CMD, missing_git_pkg)
    
    print msg
    
    after_hook()
    
    sys.exit(1)



