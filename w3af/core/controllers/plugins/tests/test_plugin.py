"""
test_plugin.py

Copyright 2006 Andres Riancho

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

from w3af.core.controllers.plugins.plugin import Plugin
from w3af.plugins.crawl.find_dvcs import find_dvcs


class TestPlugin(unittest.TestCase):
    def test_get_desc_trivial(self):
        p = Plugin()
        p.__doc__ = 'abc'

        self.assertEqual(p.get_desc(), 'abc')

    def test_get_desc_complex(self):
        p = find_dvcs()
        desc = p.get_desc()

        self.assertNotIn('author', desc)
