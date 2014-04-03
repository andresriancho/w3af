"""
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

"""
import sys
import warnings
import logging

try:
    # Is pip even there?
    import pip
    # We do this in order to check for really old versions of pip
    pip.get_installed_distributions()
except ImportError:
    print('We recommend you install pip before continuing.')
    print('http://www.pip-installer.org/en/latest/installing.html')
    HAS_PIP = False
except AttributeError:
    print('A very old version of pip was detected. We recommend you update your'
          ' your pip installation before continuing:')
    print('    sudo pip install --upgrade pip')
    HAS_PIP = False
else:
    HAS_PIP = True

from .lazy_load import lazy_load
from .utils import verify_python_version
from .helper_script import (generate_helper_script,
                            generate_pip_install_non_git,
                            generate_pip_install_git)
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
    """
    This function verifies that the dependencies that are needed by the
    framework core are met.
    
    :return: True if the process should exit
    """
    verify_python_version()
    
    disable_warnings()
    
    #
    #    Check for missing python modules
    #
    failed_deps = []
    if HAS_PIP: pip_distributions = pip.get_installed_distributions()
    
    for w3af_req in pip_packages:
        if HAS_PIP:
            dependency_specs = w3af_req.package_name, w3af_req.package_version
            for dist in pip_distributions:
                if (dist.project_name, dist.version) == dependency_specs:
                    # It's installed and the version matches!
                    break
            else:
                failed_deps.append(w3af_req)
        else:
            # The pip module is not installed (really strange for new unixes)
            try:
                if not lazy_load(w3af_req.module_name):
                    failed_deps.append(w3af_req)
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

    if not HAS_PIP:
        os_packages.extend(system_packages['PIP'])

    # All installed?
    if not failed_deps and not os_packages:
        # False means: do not exit()
        return False

    generate_requirements_txt(failed_deps)
    script_path = generate_helper_script(pkg_manager_cmd, os_packages,
                                         pip_cmd, failed_deps)

    #
    #    Report the missing system packages
    #
    msg = 'w3af\'s requirements are not met, one or more third-party'\
          ' libraries need to be installed.\n\n'
          
    if os_packages:
        missing_pkgs = ' '.join(os_packages)
        
        msg += 'On %s systems please install the following operating'\
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
        not_git_pkgs = [fdep for fdep in failed_deps if not fdep.is_git]
        git_pkgs = [fdep.git_src for fdep in failed_deps if fdep.is_git]
        
        msg = 'After installing any missing operating system packages, use'\
              ' pip to install the remaining modules:\n'
        
        if not_git_pkgs:
            cmd = generate_pip_install_non_git(pip_cmd, not_git_pkgs)
            msg += '    %s\n' % cmd
        
        if git_pkgs:
            for missing_git_pkg in git_pkgs:
                msg += '    %s\n' % generate_pip_install_git(pip_cmd, missing_git_pkg)
        
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
