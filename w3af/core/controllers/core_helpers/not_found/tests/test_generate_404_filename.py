# -*- coding: UTF-8 -*-
"""
test_generate_404_filename.py

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
from __future__ import division

import random
import unittest

from w3af.core.controllers.core_helpers.not_found.generate_404 import generate_404_filename


class TestGenerate404Filename(unittest.TestCase):
    def test_404_generation(self):

        random.seed(1)

        tests = [
            ('ab-23', 'ba-23'),
            ('abc-12', 'bac-21'),
            ('ab-23.html', 'ba-23.html'),
            ('a1a2', 'd4d5'),
            ('a1a2.html', 'd4d5.html'),
            ('hello.html', 'ehllo.html'),
            ('r57_Mohajer22.php', 'r57_oMahejr22.php'),

            # overflow handling
            ('Z', 'i0pVZ'),
        ]

        for fname, modfname in tests:
            self.assertEqual(generate_404_filename(fname), modfname)
