"""
test_disk_space_observer.py

Copyright 2015 Andres Riancho

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

from ..disk_space_observer import DiskSpaceObserver


class TestDiskSpaceObserver(unittest.TestCase):

    def test_not_raises_time_protection(self):
        observer = DiskSpaceObserver()
        observer.MIN_FREE_BYTES = 1
        observer.analyze_disk_space()

    def test_not_raises_low_requirement(self):
        observer = DiskSpaceObserver()
        observer.last_call = time.time() - observer.ANALYZE_EVERY - 1
        observer.MIN_FREE_BYTES = 1
        observer.analyze_disk_space()

    def test_raises(self):
        observer = DiskSpaceObserver()
        observer.last_call = time.time() - observer.ANALYZE_EVERY - 1
        observer.MIN_FREE_BYTES = (2 ** 52) * 1024 * 1024
        self.assertRaises(IOError, observer.analyze_disk_space)
