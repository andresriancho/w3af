"""
helper_script.py

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
import os
import tempfile

from .utils import running_in_virtualenv


SCRIPT_NAME = 'w3af_dependency_install.sh'


def generate_helper_script(pkg_manager_cmd, os_packages, pip_cmd, failed_deps,
                           external_commands):
    """
    Generates a helper script to be run by the user to install all the
    dependencies.
    
    :return: The path to the script name.
    """
    temp_dir = tempfile.gettempdir()
    
    script_path = os.path.join(temp_dir, SCRIPT_NAME)
    
    script_file = file(script_path, 'w')
    script_file.write('#!/bin/bash\n')
    
    #
    #    Report the missing system packages
    #
    if os_packages:
        missing_pkgs = ' '.join(os_packages)
        script_file.write('%s %s\n' % (pkg_manager_cmd, missing_pkgs))
        
    #
    #    Report all missing python modules
    #    
    if failed_deps:
        script_file.write('\n')

        if running_in_virtualenv():
            script_file.write('# Run without sudo to install inside venv\n')

        not_git_pkgs = [fdep for fdep in failed_deps if not fdep.is_git]
        git_pkgs = [fdep.git_src for fdep in failed_deps if fdep.is_git]
        
        if not_git_pkgs:
            cmd = generate_pip_install_non_git(pip_cmd, not_git_pkgs)
            script_file.write('%s\n' % cmd)
        
        if git_pkgs:
            for missing_git_pkg in git_pkgs:
                cmd = generate_pip_install_git(pip_cmd, missing_git_pkg)
                script_file.write('%s\n' % cmd)

    for cmd in external_commands:
        script_file.write('%s\n' % cmd)

    # Make it executable
    os.chmod(script_path, 0755)

    script_file.close()
    return script_path


def generate_pip_install_non_git(pip_cmd, not_git_pkgs):
    if running_in_virtualenv():
        cmd_fmt = '%s install %s'
    else:
        cmd_fmt = 'sudo %s install %s'

    install_specs = []
    for fdep in not_git_pkgs:
        install_specs.append('%s==%s' % (fdep.package_name,
                                         fdep.package_version))
        
    cmd = cmd_fmt % (pip_cmd, ' '.join(install_specs))
    return cmd


def generate_pip_install_git(pip_cmd, git_pkg):
    """
    :param pip_cmd: The pip command for this platform
    :param git_pkg: The name of the pip+git package
    :return: The command to be run to install the pip+git package
    """
    if running_in_virtualenv():
        cmd_fmt = '%s install --ignore-installed %s'
    else:
        cmd_fmt = 'sudo %s install --ignore-installed %s'

    return cmd_fmt % (pip_cmd, git_pkg)
