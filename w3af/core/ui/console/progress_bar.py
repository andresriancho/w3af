"""
IMPORTANT:
    This file was taken from the great sqlmap project. Only some lines were changed to adapt the code to w3af.

Copyright 2007 Andres Riancho

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
import time

import w3af.core.controllers.output_manager as om


class progress_bar(object):
    """
    This class defines methods to update and draw a progress bar.

    :author: Bernardo Damele from the sqlmap project.
    """

    def __init__(self, minValue=0, maxValue=10, totalWidth=54):
        self.__progBar = "[]"
        self.__oldProgBar = ""
        self.__min = minValue
        self.__max = maxValue
        self.__span = maxValue - minValue
        self.__width = totalWidth
        self.__amount = 0
        self.__firstAmountChangeTime = 0
        self._eta = 0
        if self.__max > self.__min:
            self.update()

    def __convertSeconds(self, value):
        seconds = value
        minutes = seconds / 60
        seconds = seconds - (minutes * 60)

        return "%.2d:%.2d" % (minutes, seconds)

    def inc(self):
        self.__amount += 1
        if not self.__firstAmountChangeTime:
            self.__firstAmountChangeTime = time.time()
        else:
            timeForAllRequests = (self.__max * (
                time.time() - self.__firstAmountChangeTime)) / self.__amount
            timeAlreadyElapsed = time.time() - self.__firstAmountChangeTime
            self._eta = timeForAllRequests - timeAlreadyElapsed
        self.update(self.__amount)
        self.draw(self._eta)

    def update(self, newAmount=0):
        """
        This method updates the progress bar
        """

        if newAmount < self.__min:
            newAmount = self.__min
        elif newAmount > self.__max:
            newAmount = self.__max

        self.__amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.__amount - self.__min)
        percentDone = (diffFromMin / float(self.__span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        # Figure out how many hash bars the percentage should be
        allFull = self.__width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # Build a progress bar with an arrow of equal signs
        if numHashes == 0:
            self.__progBar = "[>%s]" % (" " * (allFull - 1))
        elif numHashes == allFull:
            self.__progBar = "[%s]" % ("=" * allFull)
        else:
            self.__progBar = "[%s>%s]" % ("=" * (numHashes - 1),
                                          " " * (allFull - numHashes))

        # Add the percentage at the beginning of the progress bar
        percentString = str(percentDone)
        if percentDone == 100:
            percentString += "%"
        else:
            percentString += "% "

        self.__progBar = "%s %s" % (percentString, self.__progBar)

    def draw(self, eta=0):
        """
        This method draws the progress bar if it has changed
        """

        if self.__progBar != self.__oldProgBar:
            self.__oldProgBar = self.__progBar

            if eta and self.__amount < self.__max:
                om.out.console("\r%s %d/%d  ETA %s" % (self.__progBar, self.__amount, self.__max, self.__convertSeconds(int(eta))), new_line=False)
            else:
                blank = " " * (80 - len("\r%s %d/%d" % (
                    self.__progBar, self.__amount, self.__max)))
                om.out.console("\r%s %d/%d%s" % (self.__progBar, self.__amount,
                               self.__max, blank), new_line=False)

            if self.__amount == self.__max:
                om.out.console("")

    def __str__(self):
        """
        This method returns the progress bar string
        """

        return str(self.__progBar)
