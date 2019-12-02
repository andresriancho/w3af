"""
wrappers.py

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
import os
import string
from random import choice

from w3af.core.controllers.misc.temp_dir import get_temp_dir


class GenericBloomFilter(object):
    """
    A simple "interface like" class to define how a bloom filter should look
    like, methods, attributes, etc.

    The idea is to give a consistent API to all the other sections of the code
    and allow the use of different bloom filter implementations.
    """
    def __init__(self, capacity, error_rate=0.01):
        self.capacity = capacity
        self.error_rate = error_rate
        self.bf = None

    def __contains__(self, key):
        # pylint: disable=E1135
        return key in self.bf
        # pylint: enable=E1135

    def __len__(self):
        return len(self.bf)

    def __repr__(self):
        return repr(self.bf)

    def __str__(self):
        return str(self.bf)

    def add(self, key):
        return self.bf.add(key)

    @staticmethod
    def get_temp_file():
        """
        Create the temp file
        """
        tempdir = get_temp_dir()

        if not os.path.exists(tempdir):
            os.makedirs(tempdir)

        filename = ''.join([choice(string.letters) for _ in range(12)])
        temp_file = os.path.join(tempdir, filename + '-w3af.bloom')
        return temp_file
