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
# Foundation, Inc., 51 Franklin Street, Suite 500, Boston, MA  02110-1335  USA


import os
import unittest

import Halberd.ScanTask
import Halberd.clues.file
import Halberd.clues.analysis as analysis


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.threshold = Halberd.ScanTask.default_ratio_threshold

    def _hits(self, clues):
        return sum(map(lambda c: c.get_count(), clues))

    def _get_clues(self, filename):
        fname = os.path.join('tests', 'data', filename + '.clu')
        return Halberd.clues.file.load(fname)

    def analyze(self, filename, expected_raw, expected_analyzed):
        clues = self._get_clues(filename)
        self.failUnless(len(clues) >= expected_raw)

        analyzed = analysis.analyze(clues)
        analyzed = analysis.reanalyze(clues, analyzed, self.threshold)
        self.failUnlessEqual(len(analyzed), expected_analyzed)

        total_before = self._hits(clues)
        total_after = self._hits(analyzed)

        self.failUnlessEqual(total_before, total_after)

    def test_simple(self):
        self.analyze('agartha', 2, 1)

    def test_synnergy(self):
        self.analyze('www.synnergy.net', 2, 1)

    def test_tripod(self):
        self.analyze('www.tripod.com', 9, 5)

    def test_ebay(self):
        self.analyze('www.ebay.com', 2, 1)

    def test_barclays(self):
        self.analyze('www.barclays.es', 3, 2)

    def test_sohu(self):
        self.analyze('www.sohu.com', 15, 2)

    def test_dmoz(self):
        self.analyze('www.dmoz.org', 15, 3)

    def test_excite(self):
        self.analyze('email.excite.com', 30, 20)

    def test_register(self):
        self.analyze('www.register.com', 20, 1)

    def test_pricegrabber(self):
        self.analyze('www.pricegrabber.com', 20, 1)

    def test_yesky(self):
        self.analyze('www.yesky.com', 20, 1)

    def test_pogo(self):
        self.analyze('www.pogo.com', 20, 1)

    def test_macromedia(self):
        self.analyze('www.macromedia.com', 7, 4)

    def test_ask(self):
        self.analyze('www.ask.com', 3, 1)

    def test_comcast(self):
        self.analyze('www.comcast.net', 5, 2)

    def test_hotwired(self):
        self.analyze('hotwired.lycos.com', 6, 3)

    def test_passport(self):
        self.analyze('login.passport.net', 4, 2)

    def test_cdrom(self):
        self.analyze('www.cdrom.com', 4, 2)


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
