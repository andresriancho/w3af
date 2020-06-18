"""
test_chrome.py

Copyright 2018 Andres Riancho

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


from w3af.core.controllers.dependency_check.external.chrome import (get_chrome_path,
                                                                    get_chrome_version)


class TestChrome(unittest.TestCase):
    def test_get_path(self):
        chrome_path = get_chrome_path()
        self.assertIn('chrom', chrome_path)

    def test_get_version(self):
        chrome_version = get_chrome_version()
        chrome_version = chrome_version.lower()
        self.assertIn('chrom', chrome_version)
