# -*- encoding: utf-8 -*-
"""
test_make_leet.py

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

from w3af.core.controllers.misc.make_leet import make_leet


class TestMakeLeet(unittest.TestCase):

    def test_make_leet(self):
        self.assertEqual(make_leet('adminstradores'), ['admin57radore5',
                                                       '4dm1nstr4d0r3s',
                                                       '4dm1n57r4d0r35'])
        
        self.assertEqual(make_leet('pepepito'), ['pepepi7o', 'p3p3p170',
                                                 'p3p3p1t0'])
        
        self.assertEqual(make_leet('sS '), ['55 '])
