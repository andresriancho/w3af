'''
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

'''
import os
import tempfile

SCRIPT_NAME = 'w3af_dependency_install.sh'


def generate_helper_script(pkg_manager_cmd, os_packages,
                           pip_cmd, failed_deps):
    '''
    Generates a helper script to be run by the user to install all the
    dependencies.
    
    :return: The path to the script name.
    '''
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
        not_git_pkgs = [fdep.package_name for fdep in failed_deps if not fdep.is_git]
        git_pkgs = [fdep.package_name for fdep in failed_deps if fdep.is_git]
        
        if not_git_pkgs:
            cmd = 'sudo %s install %s' % (pip_cmd, ' '.join(not_git_pkgs))
            script_file.write('%s\n' % cmd)
        
        if git_pkgs:
            for missing_git_pkg in git_pkgs:
                cmd = 'sudo %s install -e %s' % (pip_cmd, missing_git_pkg)
                script_file.write('%s\n' % cmd)
    
    script_file.close()
    
    # Make it executable
    os.chmod(script_path, 0755)
    
    return script_path
