# -*- coding: iso-8859-1 -*-

"""Unit test for Halberd.clues.Clue
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Suite 500, Boston, MA  02110-1335  USA


import unittest

from Halberd.clues.Clue import Clue


class TestClue(unittest.TestCase):

    def setUp(self):
        self.clue = Clue()

    def tearDown(self):
        pass

    def test_count(self):
        self.failUnlessEqual(self.clue.get_count(), 1)
        self.clue.inc_count()
        self.failUnlessEqual(self.clue.get_count(), 2)
        self.clue.inc_count(21)
        self.failUnlessEqual(self.clue.get_count(), 23)

        self.failUnlessRaises(ValueError, self.clue.inc_count, 0)
        self.failUnlessRaises(ValueError, self.clue.inc_count, -7)

    def test_normalize(self):
        value = '123content-location*23'
        self.failUnless(Clue.normalize(value) == 'content_location_23')
        value = 'content/location'
        self.failUnless(Clue.normalize(value) == 'content_location')
        value = '*content/location123'
        self.failUnless(Clue.normalize(value) == '_content_location123')

    def test_recompute(self):
        # Check for invalid digest computations.
        self.clue.parse('Test: abc\r\nSomething: blah\r\n\r\n')
        self.assertRaises(AssertionError, self.clue._updateDigest, )


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
