# -*- coding: iso-8859-1 -*-

"""Unit test for Halberd.clues.analysis
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import os
import unittest

import Halberd.ScanTask
import Halberd.clues.file
import Halberd.clues.analysis as analysis


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.threshold = Halberd.ScanTask.default_ratio_threshold


    def _hits(self, clues):
        return sum(map(lambda c: c.getCount(), clues))

    def _getClues(self, filename):
        fname = os.path.join('tests', 'data', filename + '.clu')
        return Halberd.clues.file.load(fname)

    def analyze(self, filename, expected_raw, expected_analyzed):
        clues = self._getClues(filename)
        self.failUnless(len(clues) >= expected_raw)

        analyzed = analysis.analyze(clues)
        analyzed = analysis.reanalyze(clues, analyzed, self.threshold)
        self.failUnlessEqual(len(analyzed), expected_analyzed)

        total_before = self._hits(clues)
        total_after = self._hits(analyzed)

        self.failUnlessEqual(total_before, total_after)

    def testSimple(self):
        self.analyze('agartha', 2, 1)

    def testSynnergy(self):
        self.analyze('www.synnergy.net', 2, 1)

    def testTripod(self):
        self.analyze('www.tripod.com', 9, 5)

    def testEbay(self):
        self.analyze('www.ebay.com', 2, 1)

    def testBarclays(self):
        self.analyze('www.barclays.es', 3, 2)

    def testSohu(self):
        self.analyze('www.sohu.com', 15, 2)

    def testDmoz(self):
        self.analyze('www.dmoz.org', 15, 3)

    def testExcite(self):
        self.analyze('email.excite.com', 30, 20)

    def testRegister(self):
        self.analyze('www.register.com', 20, 1)

    def testPricegrabber(self):
        self.analyze('www.pricegrabber.com', 20, 1)

    def testYesky(self):
        self.analyze('www.yesky.com', 20, 1)

    def testPogo(self):
        self.analyze('www.pogo.com', 20, 1)

    def testMacromedia(self):
        self.analyze('www.macromedia.com', 7, 4)

    def testAsk(self):
        self.analyze('www.ask.com', 3, 1)

    def testComcast(self):
        self.analyze('www.comcast.net', 5, 2)

    def testHotwired(self):
        self.analyze('hotwired.lycos.com', 6, 3)

    def testPassport(self):
        self.analyze('login.passport.net', 4, 2)

    def testCdrom(self):
        self.analyze('www.cdrom.com', 4, 2)


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
