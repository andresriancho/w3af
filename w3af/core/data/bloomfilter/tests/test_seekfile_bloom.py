"""
test_seekfile_bloom.py

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
from w3af.core.data.bloomfilter.seekfile_bloom import FileSeekBloomFilter
from w3af.core.data.bloomfilter.tests.generic_filter_test import GenericFilterTest
from w3af.core.data.bloomfilter.wrappers import GenericBloomFilter


class TestFileSeekBloomFilterLarge(GenericFilterTest):

    CAPACITY = 20000
    ERROR_RATE = 0.001

    def setUp(self):
        super(TestFileSeekBloomFilterLarge, self).setUp()
        temp_file = GenericBloomFilter.get_temp_file()
        self.filter = FileSeekBloomFilter(self.CAPACITY, self.ERROR_RATE,
                                          temp_file)


class TestFileSeekBloomFilterSmall(GenericFilterTest):

    CAPACITY = 500
    ERROR_RATE = 0.001

    def setUp(self):
        super(TestFileSeekBloomFilterSmall, self).setUp()
        temp_file = GenericBloomFilter.get_temp_file()
        self.filter = FileSeekBloomFilter(self.CAPACITY, self.ERROR_RATE,
                                          temp_file)
