# -*- encoding: utf-8 -*-
'''
bloomfilter.py

Copyright 2011 Andres Riancho

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

'''
from core.data.bloomfilter.wrappers import GenericBloomFilter

# This import can't fail, it is pure-python love ;)
from core.data.bloomfilter.seekfile_bloom import FileSeekBloomFilter\
    as FileSeekFilter


try:
    # This might fail since it is a C library that only works in Linux
    from pybloomfilter import BloomFilter as CMmapFilter

    # There were reports of the C mmap filter not working properly in OSX,
    # just in case, I'm testing here...
    temp_file = GenericBloomFilter.get_temp_file()
    try:
        bf = CMmapFilter(1000, 0.01, temp_file)
        bf.add(1)
        assert 1 in bf
        assert 2 not in bf
    except:
        WrappedBloomFilter = FileSeekFilter
    else:
        WrappedBloomFilter = CMmapFilter

except:
    WrappedBloomFilter = FileSeekFilter


class BloomFilter(GenericBloomFilter):
    def __init__(self, capacity, error_rate):
        '''
        @param capacity: How many items you want to store, eg. 10000
        @param error_rate: The acceptable false positive rate, eg. 0.001
        '''
        GenericBloomFilter.__init__(self, capacity, error_rate)

        temp_file = self.get_temp_file()
        self.bf = WrappedBloomFilter(capacity, error_rate, temp_file)
