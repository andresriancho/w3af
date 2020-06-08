"""
test_thread_time.py

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
import unittest
import time
import hashlib

from w3af.core.controllers.profiling.thread_time import thread_active_time


class TestThreadTime(unittest.TestCase):
    def test_thread_active_time(self):
        #
        # What we want to test here is that the time measured is not the wall time
        # but the time used by the CPU to run this method. Sleep() will not require
        # much CPU cycles, thus even though we sleep for 3 seconds the spent CPU
        # time is less that 0.1
        #
        start = thread_active_time()

        time.sleep(3)

        spent = thread_active_time() - start
        self.assertLess(spent, 0.1)

    def test_thread_active_time_hash(self):
        #
        # What we want to test here is that the time measured is not the wall time
        # but the time used by the CPU to run this method. Calculating hashes will
        # require a lot of CPU cycles, thus the result returned by subtracting both
        # thread active times should be _similar_ to the wall time.
        #
        start_thread = thread_active_time()
        start_wall = time.time()

        for i in xrange(1000000):
            h = hashlib.sha512()
            h.update('%s' % i)
            h.hexdigest()

        spent_thread = thread_active_time() - start_thread
        spent_wall = time.time() - start_wall

        self.assertAlmostEqual(spent_thread, spent_wall, delta=spent_wall * 0.1)
