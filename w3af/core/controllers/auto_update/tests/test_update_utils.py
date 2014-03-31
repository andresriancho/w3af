"""
test_git_auto_update.py

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
import unittest
import subprocess

import git

from w3af.core.controllers.auto_update.utils import (is_git_repo,
                                                     get_latest_commit,
                                                     get_current_branch)


class TestGitUtils(unittest.TestCase):
    
    def test_is_git_repo(self):
        self.assertTrue(is_git_repo('.'))
    
    def test_is_git_repo_negative(self):
        self.assertFalse(is_git_repo('/etc/'))
    
    def test_get_latest_commit(self):
        latest_commit = get_latest_commit()
        
        self.assertEqual(len(latest_commit), 40)
        self.assertIsInstance(latest_commit, basestring)
        
    def test_get_latest_commit_negative(self):
        self.assertRaises(git.exc.InvalidGitRepositoryError, get_latest_commit, '/etc/')

    def test_get_current_branch(self):
        # For some strange reason jenkins creates a branch called
        # jenkins-<job name> during the build, which makes this test FAIL
        # if we don't take that into account
        
        current_branch = get_current_branch()
        
        branches = subprocess.check_output(['git', 'branch']).splitlines()
        parsed_branch = [l.strip()[2:] for l in branches if l.startswith('*')][0]
        
        self.assertEqual(current_branch, parsed_branch)
