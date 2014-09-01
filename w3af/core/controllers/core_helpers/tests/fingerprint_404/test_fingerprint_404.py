# -*- coding: UTF-8 -*-
"""
test_fingerprint_404.py

Copyright 2014 Andres Riancho

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

import unittest

from w3af.core.controllers.core_helpers.fingerprint_404 import fingerprint_404


class TestGenerate404Filename(unittest.TestCase):
    def test_404_generation(self):
        TESTS = [('ab-23', 'ba-23'),
                 ('abc-12', 'bac-21'),
                 ('ab-23.html', 'ba-23.html'),
                 ('a1a2', 'd4d5'),
                 ('a1a2.html', 'd4d5.html'),
                 ('Z', 'c'), # overflow handling
                 ('hello.html', 'ehllo.html'),
                 ]

        f404 = fingerprint_404()
        for fname, modfname in TESTS:
            self.assertEqual(f404._generate_404_filename(fname), modfname)

