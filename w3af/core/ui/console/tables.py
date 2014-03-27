"""
tables.py

Copyright 2008 Andres Riancho

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
import w3af.core.controllers.output_manager as om

from w3af.core.ui.console.io.console import terminal_width
from w3af.core.ui.console.util import formatParagraph


class table(object):
    """
    An utility class which stores the table-structured data and implements
    a clever method of drawing the tables. Ok, clever enough for our purposes.
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """
    def __init__(self, rows):
        """
        :param rows: array of arrays
        Every row is array of string (string per column)
        """
        self._rows = rows
        self._colsNum = len(self._rows[0])
        self._colsRange = range(self._colsNum)
        self._separator = '|'

    def draw(self, termWidth=terminal_width(), header=False, group=None, transf=None):
        if len(self._rows) == 0:
            return

        self._initRelWidthes(termWidth)
        self._justify()
        sl = len(self._separator)
        self._tableWidth = sum(self._widthes) + \
            self._colsNum * (sl + 2) + sl

        self.draw_br()
        for row in self._rows:
            self.draw_row(row)
            if header:
                self.draw_br()
            header = False
        self.draw_br()

    def _initRelWidthes(self, termWidth):

        ls = len(self._separator)
        space = termWidth - self._colsNum * (ls + 2) - ls  # Useful space

        #maximal length of content for every column
        maxLengths = [max([max(map(len, row[i].split('\n'))) for row in self._rows if len(row) > 0])
                      for i in self._colsRange]
        sumMaxLen = sum(maxLengths)

        # We calculate the widthes in the proportion to they longest line
        # later we justify it with the justify function
        relativeLengths = [float(ml) / sumMaxLen for ml in maxLengths]
        self._widthes = [int(rl * space) for rl in relativeLengths]

    def _justify(self):
        """
        This function reallocates widthes between columns.
        :param shift is array which contain lack or plenty of space in the column.
        Lack of space happens when a longest word in a column does not fit into originally allocated space.
        This function acts as Robin Hood: it takes excess of space from the "richest" column and gives it
        to the poorest ones.
        """
        minLengths = [max([max(map(len, row[i].split() + [''])) for row in self._rows if len(row) > 0])
                      for i in range(self._colsNum)]
        shifts = [w - mw for mw, w in zip(minLengths, self._widthes)]
        #length = len(shifts)
        borrow = zip(self._colsRange, shifts)
        borrow.sort(lambda a, b: cmp(a[1], b[1]))
        delta = [0] * self._colsNum

        donorIdx = self._colsNum - 1
        recIdx = 0
        while True:

            curDonation = borrow[donorIdx][1]
            curRec = borrow[recIdx][1]

            if curRec >= 0 or curDonation <= 0:
                break

            curDelta = min(curDonation, -curRec)
            curDonation -= curDelta
            curRec += curDelta
            delta[borrow[donorIdx][0]] -= curDelta
            delta[borrow[recIdx][0]] += curDelta

            if curDonation == 0:
                donorIdx -= 1

            if curRec == 0:
                recIdx += 1

        for i in self._colsRange:
            self._widthes[i] += delta[i]

    def draw_br(self, char='-'):
        ls = len(self._separator)
        om.out.console(self._separator + char * (self._tableWidth -
                       2 * ls) + self._separator)

    def draw_row(self, row):
        if len(row) == 0:
            self.draw_br()
            return
        columns = [formatParagraph(col, w) for col, w in zip(row,
                                                             self._widthes)]
        emptyLines = [' ' * w for w in self._widthes]
        maxHeight = max(map(len, columns))
        columns = [col + [er] * (maxHeight - len(col)) for (col,
                                                            er) in zip(columns, emptyLines)]

        # width = sum(widthes) + (len(columns)-1)*3 + 4
        s = self._separator
        for rowNum in range(0, maxHeight):
            om.out.console(s + ' '
                           + (' ' + s + ' ').join([col[rowNum] for col in columns]) + ' ' + s)
