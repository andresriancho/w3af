'''
seekfile_bloom.py

Copyright 2012 Andres Riancho

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
import os
import math

from core.data.misc import python2x3


class FileSeekBloomFilter(object):
    '''Backend storage for our "array of bits" using a file in which we seek'''

    effs = 2 ^ 8 - 1

    def __init__(self, capacity=10000, error_rate=0.001):
        self.error_rate = error_rate
        # With fewer elements, we should do very well.  With more elements, our error rate "guarantee"
        # drops rapidly.
        self.capacity = capacity

        numerator = -1 * self.capacity * math.log(self.error_rate)
        denominator = math.log(2) ** 2
        #self.num_bits_m = - int((self.capacity * math.log(self.error_rate)) / (math.log(2) ** 2))
        real_num_bits_m = numerator / denominator
        self.num_bits_m = int(math.ceil(real_num_bits_m))
        '''
        self.num_bits = num_bits
        self.num_chars = (self.num_bits + 7) // 8
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, 'O_BINARY'):
            flags |= getattr(os, 'O_BINARY')
        self.file_ = os.open(filename, flags)
        os.lseek(self.file_, self.num_chars + 1, os.SEEK_SET)
        os.write(self.file_, python2x3.null_byte)
        '''
        
    def add(self, key):
        '''Add an element to the filter'''
        for bitno in self.get_bitno_lin_comb(key):
            self.set(bitno)
    
    def get_bitno_lin_comb(self, key):
        '''Apply num_probes_k hash functions to key.  Generate the array index
        and bitmask corresponding to each result'''
    
        # This one assumes key is either bytes or str (or other list of integers)
    
        # I'd love to check for long too, but that doesn't exist in 3.2, and 2.5
        # doesn't have the numbers.Integral base type
        if hasattr(key, '__divmod__'):
            int_list = []
            temp = key
            while temp:
                quotient, remainder = divmod(temp, 256)
                int_list.append(remainder)
                temp = quotient
        elif hasattr(key[0], '__divmod__'):
            int_list = key
        elif isinstance(key[0], str):
            int_list = [ ord(char) for char in key ]
        else:
            raise TypeError('Sorry, I do not know how to hash this type')
    
        hash_value1 = self.hash1(int_list)
        hash_value2 = self.hash2(int_list)
    
        # We're using linear combinations of hash_value1 and hash_value2 to
        # obtain num_probes_k hash functions
        for probeno in range(1, self.num_probes_k + 1):
            bit_index = hash_value1 + probeno * hash_value2
            yield bit_index % self.num_bits_m

    MERSENNES1 = [ 2 ** x - 1 for x in [ 17, 31, 127 ] ]
    MERSENNES2 = [ 2 ** x - 1 for x in [ 19, 67, 257 ] ]

    def simple_hash(self, int_list, prime1, prime2, prime3):
        '''Compute a hash value from a list of integers and 3 primes'''
        result = 0
        for integer in int_list:
            result += ((result + integer + prime1) * prime2) % prime3
        return result
    
    def hash1(self, int_list):
        '''Basic hash function #1'''
        return self.simple_hash(int_list, self.MERSENNES1[0],
                                self.MERSENNES1[1], self.MERSENNES1[2])
    
    def hash2(self, int_list):
        '''Basic hash function #2'''
        return self.simple_hash(int_list, self.MERSENNES2[0],
                                self.MERSENNES2[1], self.MERSENNES2[2])

    def is_set(self, bitno):
        '''Return true iff bit number bitno is set'''
        byteno, bit_within_wordno = divmod(bitno, 8)
        mask = 1 << bit_within_wordno
        os.lseek(self.file_, byteno, os.SEEK_SET)
        char = os.read(self.file_, 1)
        if isinstance(char, str):
            byte = ord(char)
        else:
            byte = char[0]
        return byte & mask

    def set(self, bitno):
        '''set bit number bitno to true'''
        byteno, bit_within_byteno = divmod(bitno, 8)
        mask = 1 << bit_within_byteno
        os.lseek(self.file_, byteno, os.SEEK_SET)
        char = os.read(self.file_, 1)
        if isinstance(char, str):
            byte = ord(char)
            was_char = True
        else:
            byte = char[0]
            was_char = False
        byte |= mask
        os.lseek(self.file_, byteno, os.SEEK_SET)
        if was_char:
            os.write(self.file_, chr(byte))
        else:
            char = python2x3.intlist_to_binary([ byte ])
            os.write(self.file_, char)

    def clear(self, bitno):
        '''clear bit number bitno - set it to false'''

        byteno, bit_within_byteno = divmod(bitno, 8)
        mask = 1 << bit_within_byteno
        os.lseek(self.file_, byteno, os.SEEK_SET)
        char = os.read(self.file_, 1)
        if isinstance(char, str):
            byte = ord(char)
            was_char = True
        else:
            byte = int(char)
            was_char = False
        byte &= FileSeekBloomFilter.effs - mask
        os.lseek(self.file_, byteno, os.SEEK_SET)
        if was_char:
            os.write(chr(byte))
        else:
            char = python2x3.intlist_to_binary([ byte ])
            os.write(char)

    # These are quite slow ways to do iand and ior, but they should work,
    # and a faster version is going to take more time
    def __iand__(self, other):
        assert self.num_bits == other.num_bits

        for bitno in xrange(self.num_bits):
            if self.is_set(bitno) and other.is_set(bitno):
                self.set(bitno)
            else:
                self.clear(bitno)

        return self

    def __ior__(self, other):
        assert self.num_bits == other.num_bits

        for bitno in xrange(self.num_bits):
            if self.is_set(bitno) or other.is_set(bitno):
                self.set(bitno)
            else:
                self.clear(bitno)

        return self

    def close(self):
        '''Close the file'''
        os.close(self.file_)

