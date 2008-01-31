#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import os
D = os.path.join

from distutils.core import setup, Command

import Halberd.ScanTask
from Halberd.version import version


class test(Command):
    """Automated testing.

    Based upon:
    http://mail.python.org/pipermail/distutils-sig/2002-January/002714.html
    """
    description  = "test the distribution prior to install"
    
    user_options = [
        ('test-dir=', None, "directory that contains the test definitions"),
    ]
                 
    def initialize_options(self):
        self.test_dir = 'tests'    
        
    def finalize_options(self):
        build = self.get_finalized_command('build')
        self.build_purelib = build.build_purelib
        self.build_platlib = build.build_platlib
                                                                                           
    def run(self):
        import sys
        import unittest

        self.run_command('build')
        self.run_command('build_ext')

        # remember old sys.path to restore it afterwards
        old_path = sys.path[:]

        # extend sys.path
        sys.path.insert(0, self.build_purelib)
        sys.path.insert(0, self.build_platlib)
        sys.path.insert(0, D(os.getcwd(), self.test_dir))

        modules = [test[:-3] for test in os.listdir(self.test_dir) \
                     if test.startswith('test_') and test.endswith('.py')]

        loader = unittest.TestLoader()
        runner = unittest.TextTestRunner(verbosity=2)

        for module in modules:
            print "Running tests found in '%s'..." % module
            TEST = __import__(module, globals(), locals(), [])
            suite = loader.loadTestsFromModule(TEST)
            runner.run(suite)
        
        # restore sys.path
        sys.path = old_path[:]


long_description = \
r"""Halberd discovers HTTP load balancers. It is useful for web application security auditing
and for load balancer configuration testing."""

# Trove classifiers. The complete list can be grabbed from:
# http://www.python.org/pypi?:action=list_classifiers
classifiers = """\
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Information Technology
Intended Audience :: System Administrators
License :: OSI Approved :: GNU General Public License (GPL)
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Topic :: Internet :: WWW/HTTP
Topic :: Security
"""

setup(
    name = 'halberd', version = version.v_short,
    description = 'HTTP load balancer detector',
    long_description = long_description,
    author = 'Juan M. Bello Rivas',
    author_email = 'jmbr@superadditive.com',
    url = 'http://halberd.superadditive.com/',
    packages = ['Halberd', 'Halberd.clues'],
    package_dir = {'Halberd': 'Halberd'},
    scripts = [D('scripts', 'halberd')],
    data_files = [(D('man', 'man1'), \
                  [D('man', 'man1', 'halberd.1')])],
    classifiers = classifiers.splitlines(),
    cmdclass = {'test': test},
)


# vim: ts=4 sw=4 et
