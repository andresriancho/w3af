# -*- coding: iso-8859-1 -*-

"""Provides scanning patterns to be used as building blocks for more complex
scans.

Strategies are different ways in which target scans may be done. We provide
basic functionality so more complex stuff can be built upon this.
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


import Halberd.crew
import Halberd.logger
import Halberd.reportlib
import Halberd.clues.file
import Halberd.clues.analysis as analysis


class ScanError(Exception):
    """Generic error during scanning.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class BaseStrategy:
    """Defines the strategy used to scan.

    A strategy is a certain way to use the program. Theses can be layered to
    build a bigger strategy doing more complex things, etc.
    """
    def __init__(self, scantask):
        self.task = scantask
        self.logger = Halberd.logger.getLogger()

    def execute(self):
        """Executes the strategy.
        """
        pass

    # ---------------------------
    # Higher-level helper methods
    # ---------------------------

    def _scan(self):
        """Allocates a work crew of scanners and launches them on the target.
        """
        assert self.task.url and self.task.addr

        self.task.clues = []
        self.task.analyzed = []
        crew = Halberd.crew.WorkCrew(self.task)
        self.task.clues = crew.scan()

    def _analyze(self):
        """Performs clue analysis.
        """
        if len(self.task.clues) == 0:
            return

        self.task.analyzed = analysis.analyze(self.task.clues)
        self.task.analyzed = analysis.reanalyze(self.task.clues,
                                self.task.analyzed, self.task.ratio_threshold)

class UniScanStrategy(BaseStrategy):
    """Scan a single URL.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

        if not self.task.url:
            raise ScanError, 'Didn\'t provide an URL to scan'

        if self.task.addr:
            # The user passed a specific address as a parameter.
            self.addrs = [self.task.addr]
        else:
            host = Halberd.util.hostname(self.task.url)
            self.logger.info('looking up host %s... ', host)

            try:
                self.addrs = Halberd.util.addresses(host)
            except KeyboardInterrupt:
                raise ScanError, 'interrupted by the user'

            if not self.addrs:
                raise ScanError, 'unable to resolve %s' % host

            self.addrs.sort()
            self.logger.info('host lookup done.')

            if len(self.addrs) > 1:
                for addr in self.addrs:
                    #self.logger.debug('%s resolves to %s', host, addr)
                    self.logger.info('%s resolves to %s', host, addr)

    def execute(self):
        """Scans, analyzes and presents results coming a single target.
        """
        if self.task.save:
            cluedir = Halberd.clues.file.ClueDir(self.task.save)

        for self.task.addr in self.addrs:
            self._scan()

            self._analyze()
            #Halberd.reportlib.report(self.task)

            if self.task.save:
                cluedir.save(self.task.url,
                             self.task.addr,
                             self.task.clues)
            return self.task

class MultiScanStrategy(BaseStrategy):
    """Scan multiple URLs.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

        if not self.task.urlfile:
            raise ScanError, 'An urlfile parameter must be provided'

        self.urlfp = open(self.task.urlfile, 'r')

    def _targets(self, urlfp):
        """Obtain target addresses from URLs.

        @param urlfp: File where the list of URLs is stored.
        @type urlfp: C{file}

        @return: Generator providing the desired addresses.
        """
        for url in urlfp:
            if url == '\n':
                continue

            # Strip end of line character and whitespaces.
            url = url[:-1].strip()

            host = Halberd.util.hostname(url)
            if not host:
                self.logger.warn('unable to extract hostname from %s', host)
                continue

            self.logger.info('looking up host %s... ', host)
            try:
                addrs = Halberd.util.addresses(host)
            except KeyboardInterrupt:
                raise ScanError, 'interrupted by the user'
            self.logger.info('host lookup done.')

            for addr in addrs:
                yield (url, addr)

    def execute(self):
        """Launch a multiple URL scan.
        """
        cluedir = Halberd.clues.file.ClueDir(self.task.save)

        for url, addr in self._targets(self.urlfp):
            self.task.url = url
            self.task.addr = addr
            self.logger.info('scanning %s (%s)', url, addr)
            self._scan()

            cluedir.save(url, addr, self.task.clues)

            self._analyze()

            Halberd.reportlib.report(self.task)

class ClueReaderStrategy(BaseStrategy):
    """Clue reader strategy.

    Works by reading and analyzing files of previously stored clues.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

    def execute(self):
        """Reads and interprets clues.
        """
        self.task.clues = Halberd.clues.file.load(self.task.cluefile)
        self._analyze()
        self.task.url = self.task.cluefile
        Halberd.reportlib.report(self.task)
    

# vim: ts=4 sw=4 et
