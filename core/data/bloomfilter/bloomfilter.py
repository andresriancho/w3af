# -*- encoding: utf-8 -*-
'''
bloomfilter.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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


try:
    # This might fail since it is a C library that only works in Linux
    from pybloomfilter import BloomFilter as WrappedBloom
    
    class BloomFilter(GenericBloomFilter):
        def __init__(self, capacity, error_rate=0.01):
            GenericBloomFilter.__init__(self, capacity, error_rate)
            
            temp_file = self.get_temp_file()
            self.bf = WrappedBloom(capacity, error_rate, temp_file)    
except:
    from core.data.bloomfilter.bitvector_bloom import BitVectorBloomFilter\
                                                      as WrappedBloom
                                                      
    class BloomFilter(GenericBloomFilter):
        def __init__(self, capacity, error_rate=0.01):
            GenericBloomFilter.__init__(self, capacity, error_rate)
            self.bf = WrappedBloom(capacity, error_rate)
