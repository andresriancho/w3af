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
import logging

from .lazy_load import lazy_load
from .utils import verify_python_version, pip_installed
from .helper_script import generate_helper_script
from .helper_requirements_txt import generate_requirements_txt
from .platforms.current_platform import (SYSTEM_NAME,
                                         PKG_MANAGER_CMD,
                                         SYSTEM_PACKAGES,
                                         PIP_CMD,
                                         PIP_PACKAGES,
                                         os_package_is_installed,
                                         after_hook)

    
def dependency_check(pip_packages=PIP_PACKAGES, system_packages=SYSTEM_PACKAGES,
                     system_name=SYSTEM_NAME, pkg_manager_cmd=PKG_MANAGER_CMD,
                     pip_cmd=PIP_CMD, exit_on_failure=True):
    '''
    This function verifies that the dependencies that are needed by the
    framework core are met.
    
    :return: True if the process should exit
    '''
    verify_python_version()
    
    disable_warnings()
    
    #
    #    Check for missing python modules
    #
    failed_deps = []
    for w3af_dependency in pip_packages:
        try:
            if not lazy_load(w3af_dependency.module_name):
                failed_deps.append(w3af_dependency)
        except KeyboardInterrupt:
            print 'User exit with Ctrl+C.'
            sys.exit(-1)
    
    #
    #    Check for missing operating system packages
    #
    missing_os_packages = []
    for _, packages in system_packages.items():
        for package in packages:
            if not os_package_is_installed(package):
                missing_os_packages.append(package)
    
    os_packages = list(set(missing_os_packages))

    if not pip_installed():
        os_packages.extend(system_packages['PIP'])

    # All installed?
    if not failed_deps and not os_packages:
        # False means: do not exit()
        return False

    generate_requirements_txt(pkg_manager_cmd, os_packages, pip_cmd,
                              failed_deps)
    script_path = generate_helper_script(pkg_manager_cmd, os_packages,
                                         pip_cmd, failed_deps)

    #
    #    Report the missing system packages
    #
    if os_packages:
        missing_pkgs = ' '.join(os_packages)
        
        msg = 'On %s systems please install the following operating'\
              ' system packages before running the pip installer:\n'\
              '    %s %s\n' 
        print msg % (system_name, pkg_manager_cmd, missing_pkgs)
        
    #
    #    Report all missing python modules
    #    
    if failed_deps:
        msg = 'Your python installation needs the following modules'\
              ' to run w3af:\n'
        msg += '    ' + ' '.join([fdep.module_name for fdep in failed_deps])
        print msg, '\n'
        
        #
        #    Report missing pip packages
        #
        not_git_pkgs = [fdep.package_name for fdep in failed_deps if not fdep.is_git]
        git_pkgs = [fdep.package_name for fdep in failed_deps if fdep.is_git]
        
        msg = 'After installing any missing operating system packages, use pip to'\
              ' install the remaining modules:\n'
        
        if not_git_pkgs:
            msg += '    sudo %s install %s\n' % (pip_cmd, ' '.join(not_git_pkgs))
        
        if git_pkgs:
            for missing_git_pkg in git_pkgs:
                msg += '    sudo %s install -e %s\n' % (pip_cmd, missing_git_pkg)
        
        print msg
    
    msg = 'A script with these commands has been created for you at %s'
    print msg % script_path
    
    enable_warnings()
    after_hook()
    
    if exit_on_failure:
        sys.exit(1)
    else:
        return True


def disable_warnings():
    # nltk raises a warning... which I want to ignore...
    warnings.filterwarnings('ignore', '.*',)

    # scapy raises an error if tcpdump is not found in PATH
    logging.disable(logging.CRITICAL)

def enable_warnings():
    # Enable warnings once again
    warnings.resetwarnings()
    
    # re-enable the logging module
    logging.disable(logging.NOTSET)
