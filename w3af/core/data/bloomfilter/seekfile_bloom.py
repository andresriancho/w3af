"""
seekfile_bloom.py

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
import os
import math
import random
import hashlib
import struct
import mmap

from w3af.core.data.misc import python2x3
from w3af.core.data.bloomfilter.wrappers import GenericBloomFilter


class FileSeekBloomFilter(GenericBloomFilter):
    """Backend storage for our "array of bits" using a file in which we seek
    About Bloom Filters: http://en.wikipedia.org/wiki/Bloom_filter
    
    With fewer elements, we should do very well.  With more elements, our
    error rate "guarantee" drops rapidly.
    """
    def __init__(self, capacity, error_rate, temp_file):
        self.error_rate = error_rate
        self.capacity = capacity
        self.stored_items = 0

        self.num_hashes = int(math.ceil(math.log(1.0 / error_rate, 2.0)))
        bits_per_hash = int(math.ceil(
                (2.0 * capacity * abs(math.log(error_rate))) /
                (self.num_hashes * (math.log(2) ** 2))))

        self.num_bits = self.num_hashes * bits_per_hash
        self.num_chars = (self.num_bits + 7) // 8

        self._file_name = temp_file
        file_handler = open(self._file_name, 'wb')
        file_handler.write(python2x3.null_byte * self.num_chars) 
        file_handler.flush()
        
        file_handler = open(self._file_name, 'r+b')
        self._mmapped_file = mmap.mmap(file_handler.fileno(), 0)
        self._mmapped_file.seek(0)
        
        random.seed(42)
        self.hash_seeds = ([str(random.getrandbits(32)) for _ in 
                            xrange(self.num_hashes)])

    def add(self, key):
        """Add an element to the filter"""
        self.stored_items += 1

        for bitno in self.generate_bits_for_key(key):            
            self.set(bitno)

    def __len__(self):
        return self.stored_items

    def __contains__(self, key):
        """
        :return: True if key is in the filter.
        """
        for bitno in self.generate_bits_for_key(key):
            if not self.is_set(bitno):
                return False
        return True

    def to_bytes(self, key):
        """
        :return: A string representation of @key.
        """
        return unicode(key).encode("utf-8")
    
    def generate_bits_for_key(self, key):
        """
        Apply num_probes_k hash functions to key, yield each bit so that
        we can perform a bit by bit check in __contains__ and in most cases
        increase performance by not calculating all hashes.
        
        :return: A trail of bits to check in the file.
        """
        key_str = self.to_bytes(key)
        m = hashlib.md5()
        # Both algorithms pass my unittests, but with sha512 it takes 2 more
        # seconds (26 vs. 28), so I'm going to leave md5.
        #m = hashlib.sha512()
        
        for i in xrange(self.num_hashes):
            seed = self.hash_seeds[i]
            
            m.update(seed)
            m.update(key_str)
            hash_result = m.digest()
            
            long_numbers = struct.unpack('QQ', hash_result)
            #long_numbers = struct.unpack('QQQQQQQQ', hash_result)
            bitno = sum(long_numbers) % self.num_bits
            
            yield bitno

    def is_set(self, bitno):
        """Return true iff bit number bitno is set"""
        byteno, bit_within_wordno = divmod(bitno, 8)
        mask = 1 << bit_within_wordno
        self._mmapped_file.seek(byteno)
        char = self._mmapped_file.read(1)
        byte = ord(char)
        return byte & mask

    def set(self, bitno):
        """set bit number bitno to true"""
        byteno, bit_within_byteno = divmod(bitno, 8)
        mask = 1 << bit_within_byteno
        
        self._mmapped_file.seek(byteno)
        char = self._mmapped_file.read(1)
        
        byte = ord(char)
        byte |= mask
        self._mmapped_file.seek(byteno)
        self._mmapped_file.write(chr(byte))

    def close(self):
        """Close the file handler and remove the backend file."""
        self._mmapped_file.close()
        os.remove(self._file_name)