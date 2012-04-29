'''
dpCache.py

Copyright 2006 Andres Riancho

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
from __future__ import with_statement

import threading

import core.data.parsers.documentParser as documentParser
from core.controllers.misc.lru import LRU

DEBUG = False
    

class dpCache:
    '''
    This class is a document parser cache.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    LRU_LENGTH = 40
    
    def __init__(self):
        self._cache = LRU(self.LRU_LENGTH)
        self._LRULock = threading.RLock()
        
        # These are here for debugging:
        self._archive = set()
        self._from_LRU = 0.0
        self._calculated_more_than_once = 0.0
        self._total = 0.0
                
    def getDocumentParserFor(self, httpResponse):
        res = None
        
        #   Before I used md5, but I realized that it was unnecessary. I experimented a little bit with
        #   python's hash functions and this is what I got:
        #
        #   dz0@laptop:~/w3af/trunk$ python -m timeit -n 100000 -s 'import zlib; s="aaa"*1234' 'zlib.crc32(s)'
        #   100000 loops, best of 3: 6.03 usec per loop
        #   dz0@laptop:~/w3af/trunk$ python -m timeit -n 100000 -s 'import zlib; s="aaa"*1234' 'zlib.adler32(s)'
        #   100000 loops, best of 3: 3.87 usec per loop
        #   dz0@laptop:~/w3af/trunk$ python -m timeit -n 100000 -s 'import hashlib; s="aaa"*1234' 'hashlib.sha1(s).hexdigest()'
        #   100000 loops, best of 3: 16.6 usec per loop
        #   dz0@laptop:~/w3af/trunk$ python -m timeit -n 100000 -s 'import hashlib; s="aaa"*1234' 'hashlib.md5(s).hexdigest()'
        #   100000 loops, best of 3: 12.9 usec per loop
        #   dz0@laptop:~/w3af/trunk$ python -m timeit -n 100000 -s 'import hashlib; s="aaa"*1234' 'hash(s)'
        #   100000 loops, best of 3: 0.117 usec per loop
        #
        #   At first I thought that the built-in hash wasn't good enough, as it could create collisions... but...
        #   given that the LRU has only 30 positions, the real probability of a colission is too low.
        #
        self._total += 1
        hash_string = hash(httpResponse.body)
        
        with self._LRULock:
            if hash_string in self._cache:
                res = self._cache[ hash_string ]
                self._debug_in_cache(hash_string)
            else:
                # Create a new instance of dp, add it to the cache
                res = documentParser.documentParser(httpResponse)
                self._cache[ hash_string ] = res
                self._debug_not_in_cache(hash_string)
            return res
    
    def _debug_not_in_cache(self, hash_string):
        if DEBUG:
            if hash_string in self._archive:
                print hash_string,'calculated and was in archive. (harmful)'
                self._calculated_more_than_once += 1
            else:
                print hash_string,'calculated for the first time and cached. (good)'
                self._archive.add(hash_string)
                
    def _debug_in_cache(self, hash_string):
        if DEBUG:
            if hash_string in self._archive:
                print hash_string,'return from LRU and was in archive. (good)'
                self._from_LRU += 1
        
    
    def __del__(self):
        if DEBUG:
            print 'dpCache LRU rate: %s' % (self._from_LRU/self._total)
            print 'dpCache re-calculation rate: %s' % (self._calculated_more_than_once/self._total)
            print 'dpCache size: %s' % self.LRU_LENGTH
    
dpc = dpCache()
