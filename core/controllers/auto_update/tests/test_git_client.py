'''
test_git_client.py

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
import unittest

from core.controllers.misc.homeDir import W3AF_LOCAL_PATH
from core.controllers.auto_update.git_client import GitClient


class TestGitClient(unittest.TestCase):
    def test_get_URL(self):
        client = GitClient(W3AF_LOCAL_PATH)
        self.assertEqual(client.URL, 'git@github.com:andresriancho/w3af.git')