"""
test_changelog.py

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

from w3af.core.controllers.auto_update.changelog import ChangeLog


class TestChangeLog(unittest.TestCase):
    
    def test_changes_between(self):
        # Hashes from https://github.com/andresriancho/w3af/commits/threading2
        start = 'cb751e941bfa2063ebcef711642ed5d22ff9db87'
        end = '9c5f5614412dce67ac13411e1eebd754b4c6fb6a'
        
        changelog = ChangeLog(start, end)
        changes = changelog.get_changes()
        
        self.assertIsInstance(changes, list)
        self.assertEqual(len(changes), 4)
        
        self.assertIn(end, [commit.commit_id for commit in changes])
        
        last_commit = changes[-1]
        self.assertEqual(last_commit.summary, 'Minor improvement for ctrl+c handling.')
        self.assertEqual(last_commit.commit_id, '98458d69d03d705d943969e68fc6930e5bbf55ca')
        self.assertEqual(last_commit.changes, [('M', 'core/controllers/dependency_check/dependency_check.py'),])
        
        first_commit = changes[0]
        self.assertEqual(first_commit.summary, 'Removing pysvn fixes for pylint as they won\'t be used anymore')
        self.assertEqual(first_commit.commit_id, '9c5f5614412dce67ac13411e1eebd754b4c6fb6a')
        self.assertEqual(first_commit.changes, [('D', 'core/controllers/tests/pylint_plugins/pysvn_fix.py'),
                                                ('M', 'core/controllers/tests/pylint.rc')])
    
    def test_str(self):
        # Hashes from https://github.com/andresriancho/w3af/commits/threading2
        start = 'cb751e941bfa2063ebcef711642ed5d22ff9db87'
        end = '9c5f5614412dce67ac13411e1eebd754b4c6fb6a'
        
        changelog = ChangeLog(start, end)        
        changelog_str = str(changelog)
        
        self.assertTrue(changelog_str.startswith('9c5f561441: Removing pysvn fixes for'))
        self.assertIn('    D core/controllers/tests/pylint_', changelog_str)
        self.assertIn('    M core/controllers/tests/pylint.rc', changelog_str)

