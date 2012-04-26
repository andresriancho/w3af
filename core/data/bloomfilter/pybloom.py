# -*- encoding: utf-8 -*-
"""This module implements a bloom filter probabilistic data structure and
an a Scalable Bloom Filter that grows in size as your add more items to it
without increasing the false positive error_rate.

The original version requires the bitarray library [0] but in order to have a
pure python implementation of a bloom filter I modified this code in order to
use BitVector [1].

[0] http://pypi.python.org/pypi/bitarray/
[1] http://pypi.python.org/pypi/BitVector/

    >>> from pybloom import BloomFilter
    >>> f = BloomFilter(capacity=10000, error_rate=0.001)
    >>> for i in xrange(0, f.capacity):
    ...     _ = f.add(i)
    ...
    >>> 0 in f
    True
    >>> f.capacity in f
    False
    >>> len(f) <= f.capacity
    True
    >>> abs((len(f) / float(f.capacity)) - 1.0) <= f.error_rate
    True

"""
import math
import hashlib
from struct import unpack, pack, calcsize

import extlib.bitvector as bitvector

__version__ = '1.0.3'
__author__  = "Jay Baird <jay@mochimedia.com>, Bob Ippolito <bob@redivi.com>,\
               Marius Eriksen <marius@monkey.org>, Alex Brassetvik <alex@brasetvik.com>"

def make_hashfuncs(num_slices, num_bits):
    if num_bits >= (1 << 31):
        fmt_code, chunk_size = 'Q', 8
    elif num_bits >= (1 << 15):
        fmt_code, chunk_size = 'I', 4
    else:
        fmt_code, chunk_size = 'H', 2
    total_hash_bits = 8 * num_slices * chunk_size
    if total_hash_bits > 384:
        hashfn = hashlib.sha512
    elif total_hash_bits > 256:
        hashfn = hashlib.sha384
    elif total_hash_bits > 160:
        hashfn = hashlib.sha256
    elif total_hash_bits > 128:
        hashfn = hashlib.sha1
    else:
        hashfn = hashlib.md5
    fmt = fmt_code * (hashfn().digest_size // chunk_size)
    num_salts, extra = divmod(num_slices, len(fmt))
    if extra:
        num_salts += 1
    salts = [hashfn(hashfn(pack('I', i)).digest()) for i in xrange(num_salts)]
    def _make_hashfuncs(key):
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        else:
            #     FIXME: This brings some serious false positives/false negatives!
            #>>> class ooo(object):
            #...     pass
            #... 
            #>>> o = ooo()
            #>>> str(o)
            #'<__main__.ooo object at 0x7fba3b23eb10>'
            #    
            #    Maybe this should be something like cPickle.dumps() ?
            key = str(key)
        rval = []
        for salt in salts:
            h = salt.copy()
            h.update(key)
            rval.extend(uint % num_bits for uint in unpack(fmt, h.digest()))
        del rval[num_slices:]
        return rval
    return _make_hashfuncs


class BloomFilter(object):
    FILE_FMT = '<dQQQQ'

    def __init__(self, capacity, error_rate=0.001):
        """Implements a space-efficient probabilistic data structure

        capacity
            this BloomFilter must be able to store at least *capacity* elements
            while maintaining no more than *error_rate* chance of false
            positives
        error_rate
            the error_rate of the filter returning false positives. This
            determines the filters capacity. Inserting more than capacity
            elements greatly increases the chance of false positives.

        >>> b = BloomFilter(capacity=100000, error_rate=0.001)
        >>> b.add("test")
        False
        >>> "test" in b
        True

        """
        if not (0 < error_rate < 1):
            raise ValueError("Error_Rate must be between 0 and 1.")
        if not capacity > 0:
            raise ValueError("Capacity must be > 0")
        # given M = num_bits, k = num_slices, p = error_rate, n = capacity
        # solving for m = bits_per_slice
        # n ~= M * ((ln(2) ** 2) / abs(ln(P)))
        # n ~= (k * m) * ((ln(2) ** 2) / abs(ln(P)))
        # m ~= n * abs(ln(P)) / (k * (ln(2) ** 2))
        num_slices = int(math.ceil(math.log(1 / error_rate, 2)))
        # the error_rate constraint assumes a fill rate of 1/2
        # so we double the capacity to simplify the API
        bits_per_slice = int(math.ceil(
            (2 * capacity * abs(math.log(error_rate))) /
            (num_slices * (math.log(2) ** 2))))
        self._setup(error_rate, num_slices, bits_per_slice, capacity, 0)
        self.bitvector = bitvector.BitVector(size=self.num_bits)
        self.bitvector.reset(0)

    def _setup(self, error_rate, num_slices, bits_per_slice, capacity, count):
        self.error_rate = error_rate
        self.num_slices = num_slices
        self.bits_per_slice = bits_per_slice
        self.capacity = capacity
        self.num_bits = num_slices * bits_per_slice
        self.count = count
        #print '\n'.join('%s = %s' % tpl for tpl in sorted(self.__dict__.items()))
        self.make_hashes = make_hashfuncs(self.num_slices, self.bits_per_slice)

    def __contains__(self, key):
        """Tests a key's membership in this bloom filter.

        >>> b = BloomFilter(capacity=100)
        >>> b.add("hello")
        False
        >>> "hello" in b
        True

        """
        bits_per_slice = self.bits_per_slice
        bitvector = self.bitvector
        if not isinstance(key, list):
            hashes = self.make_hashes(key)
        else:
            hashes = key
        offset = 0
        for k in hashes:
            if not bitvector[offset + k]:
                return False
            offset += bits_per_slice
        return True

    def __len__(self):
        """Return the number of keys stored by this bloom filter."""
        return self.count

    def add(self, key, skip_check=False):
        """ Adds a key to this bloom filter. If the key already exists in this
        filter it will return True. Otherwise False.

        >>> b = BloomFilter(capacity=100)
        >>> b.add("hello")
        False
        >>> b.add("hello")
        True

        """
        bitvector = self.bitvector
        bits_per_slice = self.bits_per_slice
        hashes = self.make_hashes(key)
        if not skip_check and hashes in self:
            return True
        if self.count > self.capacity:
            raise IndexError("BloomFilter is at capacity")
        offset = 0
        for k in hashes:
            self.bitvector[offset + k] = 1
            offset += bits_per_slice
        self.count += 1
        return False

    '''
    def tofile(self, f):
        """Write the bloom filter to file object `f'. Underlying bits
        are written as machine values. This is much more space
        efficient than pickling the object."""
        f.write(pack(self.FILE_FMT, self.error_rate, self.num_slices,
                     self.bits_per_slice, self.capacity, self.count))
        self.bitarray.tofile(f)

    @classmethod
    def fromfile(cls, f, n=-1):
        """Read a bloom filter from file-object `f' serialized with
        ``BloomFilter.tofile''. If `n' > 0 read only so many bytes."""
        headerlen = calcsize(cls.FILE_FMT)

        if 0 < n < headerlen:
            raise ValueError, 'n too small!'

        filter = cls(1)  # Bogus instantiation, we will `_setup'.
        filter._setup(*unpack(cls.FILE_FMT, f.read(headerlen)))
        filter.bitarray = bitarray.bitarray(endian='little')
        if n > 0:
            filter.bitarray.fromfile(f, n - headerlen)
        else:
            filter.bitarray.fromfile(f)
        if filter.num_bits != filter.bitarray.length() and \
               (filter.num_bits + (8 - filter.num_bits % 8)
                != filter.bitarray.length()):
            raise ValueError, 'Bit length mismatch!'

        return filter
    '''

    def __getstate__(self):
        d = self.__dict__.copy()
        del d['make_hashes']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.make_hashes = make_hashfuncs(self.num_slices, self.bits_per_slice)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
