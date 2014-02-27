"""
test_is_private_site.py

Copyright 2008 Andres Riancho

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

from w3af.core.controllers.misc.is_private_site import is_private_site


class TestIsPrivateSite(unittest.TestCase):
    def test_is_private_site_true_case01(self):
        self.assertTrue(is_private_site('127.0.0.1'))
        
    def test_is_private_site_true_case02(self):
        self.assertTrue(is_private_site('192.168.0.1'))
    
    def test_is_private_site_true_case03(self):
        self.assertTrue(is_private_site('www.w3af-scanner.org'))
    
    def test_is_private_site_false_case01(self):
        self.assertFalse(is_private_site('192.1.0.1'))

    def test_is_private_site_false_case02(self):
        self.assertFalse(is_private_site('www.w3af.org'))
        
