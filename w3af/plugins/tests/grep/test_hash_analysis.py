"""
test_hash_analysis.py

Copyright 2012 Andres Riancho

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


from w3af.plugins.grep.hash_analysis import hash_analysis


class TestHashAnalysis(unittest.TestCase):

    def test_hash_analysis(self):
        p = hash_analysis()
        self.assertTrue(
            p._has_hash_distribution('cdf13c6f85b216a18665e7bba74cc1a7'))

        self.assertFalse(
            p._has_hash_distribution('AB_Halloween_Wallpaper_1920x1080'))

        # Note the "h" at the beginning
        self.assertFalse(
            p._has_hash_distribution('hdf13c6f85b216a18665e7bba74cc1a7'))
