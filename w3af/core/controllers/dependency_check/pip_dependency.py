"""
pip_dependency.py

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


class PIPDependency(object):
    def __init__(self, module_name, package_name, package_version, git_src=None,
                 tgz_src=None):
        self.module_name = module_name
        self.package_name = package_name
        self.package_version = package_version

        self.is_git = False
        self.git_src = None
        self.tgz_src = None
                    
        if git_src is not None:
            self.is_git = True
            self.git_src = git_src
            self.tgz_src = tgz_src

    def __eq__(self, other):
        return (self.module_name == other.module_name and
                self.package_name == other.package_name and
                self.package_version == other.package_version and
                self.is_git == other.is_git and
                self.git_src == other.git_src and
                self.tgz_src == other.tgz_src)

    def __repr__(self):
        return '<PIPDependency (%s|%s)>' % (self.package_name,
                                            self.package_version)