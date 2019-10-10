# -*- encoding: utf-8 -*-
"""
test_acora_vs_esm.py

Copyright 2017 Andres Riancho

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
import esm
#import ahocorasick

from acora import AcoraBuilder, PyAcora
from nose.plugins.skip import SkipTest

from .test_data import HTTP_RESPONSE, SQL_ERRORS


@SkipTest
class TestAcoraPerformanceVsESM(unittest.TestCase):
    """
    Comment the @SkipTest and then run:

    nosetests --with-timer -s -v -x w3af/core/data/quick_match/tests/test_acora_vs_esm.py
    """

    ITERATIONS = 100000

    def test_pyahocorasick(self):
        # pylint: disable=E0602
        autom = ahocorasick.Automaton()

        for idx, (key,) in enumerate(SQL_ERRORS):
            autom.add_word(key, (idx, key))

        autom.make_automaton()

        i = 0

        for j in xrange(self.ITERATIONS):
            for end_index, (insert_order, original_value) in autom.iter(HTTP_RESPONSE):
                i += 1

        self.assertEqual(i, self.ITERATIONS * 2)

    def test_acora(self):
        builder = AcoraBuilder()
        builder.update([s for (s,) in SQL_ERRORS])
        ac = builder.build()

        i = 0

        #
        # This takes around 0.6 seconds in my workstation.
        #
        for j in xrange(self.ITERATIONS):
            for _ in ac.finditer(HTTP_RESPONSE):
                i += 1

        self.assertEqual(i, self.ITERATIONS * 2)

    def test_acora_python(self):
        builder = AcoraBuilder()
        builder.update([s for (s,) in SQL_ERRORS])
        ac = builder.build(acora=PyAcora)

        i = 0

        #
        # This takes around 9 seconds in my workstation.
        #
        for j in xrange(self.ITERATIONS):
            for _ in ac.finditer(HTTP_RESPONSE):
                i += 1

        self.assertEqual(i, self.ITERATIONS * 2)

    def test_esm(self):
        index = esm.Index()

        for (s,) in SQL_ERRORS:
            index.enter(s)

        index.fix()

        i = 0

        #
        # This takes around 5 seconds in my workstation.
        #
        for j in xrange(self.ITERATIONS):
            for _ in index.query(HTTP_RESPONSE):
                i += 1

        self.assertEqual(i, self.ITERATIONS * 2)
