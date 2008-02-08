# -*- coding: iso-8859-1 -*-

"""\
Work crew pattern of parallel scanners
======================================

Overview
--------

A work crew is instantiated passing a ScanTask object as a parameter, thus
defining the target and the way the scanning should be done. After the
initialization of the work crew it can be used to scan the target and get the
obtained clues back.

    >>> crew = WorkCrew(scantask)
    >>> clues = crew.scan()

Requirements
------------

These are the features that the WorkCrew must provide:

    1. There are 3 different types of consumers:
        - Controller thread (Performs timing + error-checking).
        - Local scanning thread.
        - Remote scanning thread.

    2. We need a way to signal:
        - When a fatal error has happened.
        - When the user has pressed Control-C

Types of scanning threads
-------------------------

The WorkCrew object spawns different kinds of threads. Here's a brief summary
of what they do:

    - Manager: Detects when the time for performing the scan has expired
    and notifies the rest of the threads. This code is executed in the main
    thread in order to be able to appropriately catch signals, etc.

    - Scanner: Performs a load-balancer scan from the current machine.

The following is a diagram showing the way it works::

                                     .--> Manager --.
                                     |              |
                                     +--> Scanner --+
        .----------.   .----------.  |              |   .-------.
 IN --> | ScanTask |->-| WorkCrew |--+--> Scanner --+->-| Clues |--> OUT
        `----------'   `----------'  |              |   `-------'
                                     +--> Scanner --+
                                     |              |
                                     `--> Scanner --'
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


import sys
import time
import math
import copy
import signal
import threading

import Halberd.logger
import Halberd.clues.Clue
import Halberd.clientlib as clientlib


__all__ = ['WorkCrew']


class ScanState:
    """Shared state among scanner threads.

    @ivar shouldstop: Signals when the threads should stop scanning.
    @type shouldstop: C{threading.Event}

    caught with an exception).
    """
    def __init__(self):
        """Initializes shared state among scanning threads.
        """
        self.__mutex = threading.Lock()
        self.shouldstop = threading.Event()
        self.__error = None
        self.__clues = []

        self.__missed = 0
        self.__replies = 0

    def getStats(self):
        """Provides statistics about the scanning process.

        @return: Number of clues gathered so far, number of successful requests
        and number of unsuccessful ones (missed replies).
        @rtype: C{tuple}
        """
        # xxx - I badly need read/write locks.
        self.__mutex.acquire()
        nclues = len(self.__clues)
        replies = self.__replies
        missed = self.__missed
        self.__mutex.release()

        return (nclues, replies, missed)

    def insertClue(self, clue):
        """Inserts a clue in the list if it is new.
        """
        self.__mutex.acquire()

        count = clue.getCount()
        self.__replies += count
        try:
            idx = self.__clues.index(clue)
            self.__clues[idx].incCount(count)
        except ValueError:
            self.__clues.append(clue)

        self.__mutex.release()

    def getClues(self):
        """Clue accessor.

        @return: A copy of all obtained clues.
        @rtype: C{list}
        """
        self.__mutex.acquire()
        clues = self.__clues[:]
        self.__mutex.release()

        return clues

    def incMissed(self):
        """Increase the counter of missed replies.
        """
        self.__mutex.acquire()
        self.__missed += 1
        self.__mutex.release()

    def setError(self, err):
        """Signal an error condition.
        """
        self.__mutex.acquire()
        if self.__error is not None:
            # An error has already been signalled.
            self.__mutex.release()
            return
        self.__error = err
        self.shouldstop.set()
        self.__mutex.release()

    def getError(self):
        """Returns the reason of the error condition.
        """
        self.__mutex.acquire()
        # Since we don't know what the nature of __error will be, we need to
        # provide a clean copy of it to the caller so that no possible
        # references or changes to __error can affect the object we return.
        err = copy.deepcopy(self.__error)
        self.__mutex.release()

        return err


class WorkCrew:
    """Pool of scanners working in parallel.

    @ivar task: A reference to scantask.
    @type task: L{ScanTask}

    @ivar working: Indicates whether the crew is working or idle.
    @type working: C{bool}

    @ivar prev: Previous SIGINT handler.
    """
    def __init__(self, scantask):
        self.workers = []
        self.task = scantask

        self.state = ScanState()

        self.working = False

        self.prev = None
        
    def _setupSigHandler(self):
        """Performs what's needed to catch SIGINT.
        """
        def interrupt(signum, frame):
            """SIGINT handler
            """
            self.state.setError('received SIGINT')

        self.prev = signal.signal(signal.SIGINT, interrupt) 

    def _restoreSigHandler(self):
        """Restore previous SIGINT handler.
        """
        signal.signal(signal.SIGINT, self.prev)

    def _initLocal(self):
        """Initializes conventional (local) scanner threads.
        """
        for i in xrange(self.task.parallelism):
            worker = Scanner(self.state, self.task)
            self.workers.append(worker)

    def scan(self):
        """Perform a parallel load-balancer scan.
        """
        self.working = True
        #self._setupSigHandler()

        self._initLocal()

        for worker in self.workers:
            worker.start()

        # The Manager executes in the main thread WHILE the others are working
        # so that signals are correctly caught.
        manager = Manager(self.state, self.task)
        manager.run()

        for worker in self.workers:
            worker.join()

        # Display status information for the last time.
        manager.showStats()
        sys.stdout.write('\n\n')

        #self._restoreSigHandler()
        self.working = False

        err = self.state.getError()
        if err is not None:
            sys.stderr.write('*** finished (%s) ***\n\n' % err)

        return self._getClues()

    def _getClues(self):
        """Returns a sequence of clues obtained during the scan.
        """
        assert not self.working

        return self.state.getClues()


class BaseScanner(threading.Thread):
    """Base class for load balancer scanning threads.

    @ivar timeout: Time (in seconds since the UNIX Epoch) when the scan will be
    stopped.
    @type timeout: C{float}
    """
    def __init__(self, state, scantask):
        """Initializes the scanning thread.

        @param state: Container to store the results of the scan (shared among
        scanning threads).
        @type state: C{instanceof(ScanState)}

        @param scantask: Object providing information needed to perform the
        scan.
        @type scantask: C{instanceof(ScanTask)}
        """
        threading.Thread.__init__(self)
        self.state = state
        self.task = scantask
        self.timeout = 0
        self.logger = Halberd.logger.getLogger()

    def remaining(self, end=None):
        """Seconds left until a given point in time.

        @param end: Ending time.
        @type end: C{float}

        @return: Remaining time until L{self.timeout}
        @rtype: C{int}
        """
        if not end:
            end = self.timeout
        return int(end - time.time())

    def hasExpired(self):
        """Expiration predicate.

        @return: True if the timeout has expired, False otherwise.
        @rtype: C{bool}
        """
        return (self.remaining() <= 0)

    def setTimeout(self, secs):
        """Compute an expiration time.

        @param secs: Amount of seconds to spend scanning the target.
        @type secs: C{int}

        @return: The moment in time when the task expires.
        @rtype: C{float}
        """
        self.timeout = time.time() + secs

    def run(self):
        """Perform the scan.
        """
        self.setTimeout(self.task.scantime)

        while not self.state.shouldstop.isSet():
            self.process()

    def process(self):
        """Perform a scanning task.

        This method should be overriden to do actual work.
        """
        pass

class Scanner(BaseScanner):
    """Scans the target host from the local machine.
    """
    def process(self):
        """Gathers clues connecting directly to the target web server.
        """
        client = clientlib.clientFactory(self.task)

        fatal_exceptions = (
            clientlib.ConnectionRefused,
            clientlib.UnknownReply,
            clientlib.HTTPSError,
        )

        try:
            ts, hdrs = client.getHeaders(self.task.addr, self.task.url)
        except fatal_exceptions, msg:
            self.state.setError(msg)
        except clientlib.TimedOut, msg:
            self.state.incMissed()
        else:
            self.state.insertClue(self.makeClue(ts, hdrs))

    def makeClue(self, timestamp, headers):
        """Compose a clue object.

        @param timestamp: Time when the reply was received.
        @type timestamp: C{float}

        @param headers: MIME headers coming from an HTTP response.
        @type headers: C{str}

        @return: A valid clue
        @rtype: C{Clue}
        """
        clue = Halberd.clues.Clue.Clue()
        clue.setTimestamp(timestamp)
        clue.parse(headers)

        return clue


class Manager(BaseScanner):
    """Performs management tasks during the scan.
    """
    # Indicates how often the state must be refreshed (in seconds).
    refresh_interval = 0.25

    def process(self):
        """Controls the whole scanning process.

        This method checks when the timeout has expired and notifies the rest
        of the scanning threads that they should stop. It also displays (in
        case the user asked for it) detailed information regarding the process.
        """
        self.showStats()

        if self.hasExpired():
            self.state.shouldstop.set()
        try:
            time.sleep(self.refresh_interval)
        except IOError:
            # Catch interrupted system call exception (it happens when
            # CONTROL-C is pressed on win32 systems).
            self.state.shouldstop.set()

    def showStats(self):
        """Displays certain statistics while the scan is happening.
        """
        if not self.task.verbose:
            return

        def statbar(elapsed, total):
            """Compose a status bar string showing progress.
            """
            done = int(math.floor(float(total - elapsed)/total * 10))
            notdone = int(math.ceil(float(elapsed)/total * 10))
            return '[' + '#' * done + ' ' * notdone + ']'

        nclues, replies, missed = self.state.getStats()

        # We put a lower bound on the remaining time.
        if self.remaining() < 0:
            remaining = 0
        else:
            remaining = self.remaining()

        statusline = '\r' + self.task.addr.ljust(15) + \
                    '  %s  clues: %3d | replies: %3d | missed: %3d' \
                    % (statbar(remaining, self.task.scantime),
                       nclues, replies, missed)
        sys.stdout.write(statusline)
        sys.stdout.flush()


# vim: ts=4 sw=4 et
