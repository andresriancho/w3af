# -*- encoding: utf-8 -*-
"""
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

"""
from w3af.core.data.bloomfilter.wrappers import GenericBloomFilter
from w3af.core.controllers.dependency_check.platforms.mac import MacOSX

# This import can't fail, it is pure-python love ;)
from w3af.core.data.bloomfilter.seekfile_bloom import FileSeekBloomFilter\
    as FileSeekFilter

if MacOSX.is_current_platform():
    # Awful workaround for Mac OS X:
    # https://github.com/andresriancho/w3af/issues/485
    WrappedBloomFilter = FileSeekFilter

    OSX_MSG = """
    w3af runs slower on Mac OS X.

    We need OS X contributors that can spend a couple of hours helping the
    pybloomfiltermmap [1] project improve their packaging for Mac. Contribute
    to make both pybloomfiltermmap and w3af better!

    For more information about this issue please visit [0][1].

    [0] https://github.com/andresriancho/w3af/issues/485
    [1] https://github.com/axiak/pybloomfiltermmap/issues/50
    """
    print(OSX_MSG)
else:
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
        """
        :param capacity: How many items you want to store, eg. 10000
        :param error_rate: The acceptable false positive rate, eg. 0.001
        """
        GenericBloomFilter.__init__(self, capacity, error_rate)

        temp_file = self.get_temp_file()
        self.bf = WrappedBloomFilter(capacity, error_rate, temp_file)
