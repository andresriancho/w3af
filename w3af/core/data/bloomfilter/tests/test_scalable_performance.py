"""
test_scalable_performance.py

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

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.disk_set import DiskSet


class TestScalablePerformance(unittest.TestCase):
    def test_bloom_filter(self):
        f = ScalableBloomFilter()

        for i in xrange(20000):
            data = (i, i)
            f.add(data)

        for i in xrange(20000):
            data = (i, i)
            data in f

    def test_disk_set(self):
        ds = DiskSet()

        for i in xrange(20000):
            data = (i, i)
            ds.add(data)

        for i in xrange(20000):
            data = (i, i)
            data in ds

