"""
test_scalable_bloom.py

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
from nose.plugins.attrib import attr

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.bloomfilter.tests.generic_filter_test import GenericFilterTest
from w3af.core.data.bloomfilter.seekfile_bloom import FileSeekBloomFilter
from w3af.core.data.bloomfilter.wrappers import GenericBloomFilter


class WrappedFileSeekBloomFilter(GenericBloomFilter):
    def __init__(self, capacity, error_rate):
        """
        :param capacity: How many items you want to store, eg. 10000
        :param error_rate: The acceptable false positive rate, eg. 0.001
        """
        GenericBloomFilter.__init__(self, capacity, error_rate)

        temp_file = self.get_temp_file()
        self.bf = FileSeekBloomFilter(capacity, error_rate, temp_file)


@attr('smoke')
class TestScalableBloomFilterLargeCmmap(GenericFilterTest):

    CAPACITY = 20000

    def setUp(self):
        super(TestScalableBloomFilterLargeCmmap, self).setUp()
        self.filter = ScalableBloomFilter(
            mode=ScalableBloomFilter.LARGE_SET_GROWTH)


class TestScalableBloomfilterSmallCmmap(GenericFilterTest):

    CAPACITY = 500

    def setUp(self):
        super(TestScalableBloomfilterSmallCmmap, self).setUp()
        self.filter = ScalableBloomFilter(
            mode=ScalableBloomFilter.LARGE_SET_GROWTH)


class TestScalableBloomFilterLargeSeekFile(GenericFilterTest):

    CAPACITY = 20000

    def setUp(self):
        super(TestScalableBloomFilterLargeSeekFile, self).setUp()
        self.filter = ScalableBloomFilter(
            mode=ScalableBloomFilter.LARGE_SET_GROWTH,
            filter_impl=WrappedFileSeekBloomFilter)


@attr('smoke')
class TestScalableBloomfilterSmallSeekFile(GenericFilterTest):

    CAPACITY = 500

    def setUp(self):
        super(TestScalableBloomfilterSmallSeekFile, self).setUp()
        self.filter = ScalableBloomFilter(
            mode=ScalableBloomFilter.LARGE_SET_GROWTH,
            filter_impl=WrappedFileSeekBloomFilter)
