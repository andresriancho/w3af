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

# Generic imports,
import os
import string
from random import choice
from core.controllers.misc.temp_dir import get_temp_dir

#
#    This import should never fail
#
from core.data.bloomfilter.pybloom import BloomFilter as pure_python_filter

#
#    This might fail...
#
try:
    from pybloomfilter import BloomFilter as mmap_filter
except:
    USE_PURE_PYTHON_FILTER = True
else:
    USE_PURE_PYTHON_FILTER = False


class generic_bloomfilter(object):
    '''
    A simple "interface like" class to define how a bloom filter should look
    like, methods, attributes, etc.
    
    The idea is to give a consistent API to all the other sections of the code
    and allow the use of different bloom filter implementations.
    '''
    def __init__(self, capacity, error_rate=0.01):
        self.capacity = capacity
        self.error_rate = error_rate
    
    def __contains__(self, key):
        raise NotImplementedError()
        
    def __len__(self):
        raise NotImplementedError()
        
    def add(self, key):
        raise NotImplementedError()

class mmap_filter_wrapper(generic_bloomfilter):
    def __init__(self, capacity, error_rate=0.01):
        generic_bloomfilter.__init__(self, capacity, error_rate)
        
        #
        #    Create the temp file
        #
        tempdir = get_temp_dir()
        if not os.path.exists( tempdir ):
            os.makedirs( tempdir )
        filename = ''.join([choice(string.letters) for i in range(12)]) + '.w3af.bloom'
        temp_file = os.path.join(tempdir, filename)
        
        self.bf = mmap_filter(capacity, error_rate, temp_file)

    def __contains__(self, key):
        return key in self.bf
        
    def __len__(self):
        return len(self.bf)
        
    def add(self, key):
        return self.bf.add( key )
        
class pure_python_filter_wrapper(generic_bloomfilter):
    def __init__(self, capacity, error_rate=0.01):
        generic_bloomfilter.__init__(self, capacity, error_rate)
        self.bf = pure_python_filter(capacity, error_rate)

    def __contains__(self, key):
        return key in self.bf
        
    def __len__(self):
        return len(self.bf)
        
    def add(self, key):
        return self.bf.add( key )

if USE_PURE_PYTHON_FILTER:
    #
    #    Easier to install (embedded in extlib) but slow and memory hungry. 
    #
    bloomfilter = pure_python_filter_wrapper
else:
    #
    #    Faster!
    #
    bloomfilter = mmap_filter_wrapper
    

class scalable_bloomfilter(object):
    SMALL_SET_GROWTH = 2 # slower, but takes up less memory
    LARGE_SET_GROWTH = 4 # faster, but takes up more memory faster

    def __init__(self, initial_capacity=1000, error_rate=0.001,
                 mode=SMALL_SET_GROWTH):
        """Implements a space-efficient probabilistic data structure that
        grows as more items are added while maintaining a steady false
        positive rate

        initial_capacity
            the initial capacity of the filter
        error_rate
            the error_rate of the filter returning false positives. This
            determines the filters capacity. Going over capacity greatly
            increases the chance of false positives.
        mode
            can be either scalable_bloomfilter.SMALL_SET_GROWTH or
            scalable_bloomfilter.LARGE_SET_GROWTH. SMALL_SET_GROWTH is slower
            but uses less memory. LARGE_SET_GROWTH is faster but consumes
            memory faster.

        >>> b = scalable_bloomfilter(initial_capacity=512, error_rate=0.001, \
                                    mode=scalable_bloomfilter.SMALL_SET_GROWTH)
        >>> b.add("test")
        False
        >>> "test" in b
        True
        >>> unicode_string = u'¡'
        >>> b.add(unicode_string)
        False
        >>> unicode_string in b
        True
        
        >>> sbf = scalable_bloomfilter(mode=scalable_bloomfilter.SMALL_SET_GROWTH)
        >>> count = 10000
        >>> for i in xrange(0, count):
        ...     _ = sbf.add(i)
        ...
        >>> sbf.capacity > count
        True
        >>> len(sbf) <= count
        True
        >>> abs((len(sbf) / float(count)) - 1.0) <= sbf.error_rate
        True
        """
        if not error_rate or error_rate < 0:
            raise ValueError("Error_Rate must be a decimal less than 0.")
        self._setup(mode, 0.9, initial_capacity, error_rate)
        self.filters = []

    def _setup(self, mode, ratio, initial_capacity, error_rate):
        self.scale = mode
        self.ratio = ratio
        self.initial_capacity = initial_capacity
        self.error_rate = error_rate

    def __contains__(self, key):
        """Tests a key's membership in this bloom filter.

        >>> b = scalable_bloomfilter(initial_capacity=100, error_rate=0.001, \
                                    mode=scalable_bloomfilter.SMALL_SET_GROWTH)
        >>> b.add("hello")
        False
        >>> "hello" in b
        True

        """
        for f in reversed(self.filters):
            if key in f:
                return True
        return False

    def add(self, key):
        """Adds a key to this bloom filter.
        If the key already exists in this filter it will return True.
        Otherwise False.

        >>> b = scalable_bloomfilter(initial_capacity=100, error_rate=0.001, \
                                    mode=scalable_bloomfilter.SMALL_SET_GROWTH)
        >>> b.add("hello")
        False
        >>> b.add("hello")
        True

        """
        if key in self:
            return True
        filter = self.filters[-1] if self.filters else None
        if filter is None or len(filter) >= filter.capacity:
            num_filters = len(self.filters)
            filter = bloomfilter(
                capacity=self.initial_capacity * (self.scale ** num_filters),
                error_rate=self.error_rate * (self.ratio ** num_filters))
            self.filters.append(filter)
        filter.add(key)
        return False

    @property
    def capacity(self):
        """Returns the total capacity for all filters in this SBF"""
        return sum([f.capacity for f in self.filters])

    @property
    def count(self):
        return len(self)

    def __len__(self):
        """Returns the total number of elements stored in this SBF"""
        return sum([len(f) for f in self.filters])
