"""
test_timeout_function.py

Copyright 2012 Andres Riancho

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
import sys
import time
import threading  # PYCHOK expected

from w3af.core.controllers.threads.timeout_function import (
    timelimited, TimeLimited,
    TimeLimitExpired)


class TestTimeoutFunction(unittest.TestCase):

    def _check(self, timeout, sleep, result, arg='OK'):
        """
        Utility function that helps with the assertions.
        """
        if timeout > sleep:
            x = None  # time.sleep(0) result
        elif isinstance(result, TimeLimitExpired):
            x = result
        else:
            x = TimeLimitExpired

        self.assertTrue(result is x)

    def test_timelimited_function(self):
        for t, s in ((2.0, 1),
                     (1.0, 20)):  # note, 20!
            try:
                r = timelimited(t, time.sleep, s)
            except Exception, e:  # XXX as for Python 3.0
                r = e
            self._check(t, s, r, timelimited)

    def test_timeLimited_class_and_property(self):
        f = TimeLimited(time.sleep)
        for t, s in ((2.0, 1),
                     (1.0, 20)):  # note, 20!
            f.timeout = t
            try:
                r = f(s)
            except Exception, e:  # XXX as for Python 3.0
                r = e
            self._check(t, s, r, f)

    def test_TypeError(self):
        try:
            t = timelimited(0, None)
            self.assertTrue(False)
        except TypeError:
            pass

    def test_ValueError(self):
        try:
            t = timelimited(-10, time.time)
            self.assertTrue(False)
        except ValueError:
            pass

    def test_error_passing_from_thread(self):
        try:
            r = timelimited(1, lambda x: 1 / x, 0)
            self.assertTrue(False)
        except ZeroDivisionError:
            pass

    def test_all_created_threads_stopped(self):
        for t in threading.enumerate():
            if t.isAlive() and repr(t).startswith('<_Timelimited('):
                self.assertTrue(False, 'Thread %r still alive' % t)
