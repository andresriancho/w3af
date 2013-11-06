'''
helper_requirements_txt.py

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
from w3af.core.controllers.ci.only_ci_decorator import only_ci

REQUIREMENTS_TXT = 'requirements.txt'


@only_ci
def generate_requirements_txt(pkg_manager_cmd, os_packages,
                                 pip_cmd, failed_deps):
    '''
    We want to generate a requirements.txt file which can be detected
    by our build system in order to install the required modules.
    
    This code should only run on CircleCI
    
    :return: The path to the script name.
    '''
    req_file = file(REQUIREMENTS_TXT, 'w')
    
    #
    #    Report all missing python modules
    #    
    if failed_deps:
        missing_modules = [fdep.package_name for fdep in failed_deps]
        
        for module in missing_modules:
            req_file.write('%s\n' % module)
        
    req_file.close()
    return REQUIREMENTS_TXT