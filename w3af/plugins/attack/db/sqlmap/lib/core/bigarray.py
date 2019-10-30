#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

try:
   import cPickle as pickle
except:
   import pickle

import itertools
import os
import sys
import tempfile
import zlib

from lib.core.enums import MKSTEMP_PREFIX
from lib.core.exception import SqlmapSystemException
from lib.core.settings import BIGARRAY_CHUNK_SIZE
from lib.core.settings import BIGARRAY_COMPRESS_LEVEL

DEFAULT_SIZE_OF = sys.getsizeof(object())

def _size_of(object_):
    """
    Returns total size of a given object_ (in bytes)
    """

    retval = sys.getsizeof(object_, DEFAULT_SIZE_OF)

    if isinstance(object_, dict):
        retval += sum(_size_of(_) for _ in itertools.chain.from_iterable(object_.items()))
    elif hasattr(object_, "__iter__"):
        retval += sum(_size_of(_) for _ in object_)

    return retval

class Cache(object):
    """
    Auxiliary class used for storing cached chunks
    """

    def __init__(self, index, data, dirty):
        self.index = index
        self.data = data
        self.dirty = dirty

class BigArray(list):
    """
    List-like class used for storing large amounts of data (disk cached)
    """

    def __init__(self):
        self.chunks = [[]]
        self.chunk_length = sys.maxint
        self.cache = None
        self.filenames = set()
        self._os_remove = os.remove
        self._size_counter = 0

    def append(self, value):
        self.chunks[-1].append(value)

        if self.chunk_length == sys.maxint:
            self._size_counter += _size_of(value)
            if self._size_counter >= BIGARRAY_CHUNK_SIZE:
                self.chunk_length = len(self.chunks[-1])
                self._size_counter = None

        if len(self.chunks[-1]) >= self.chunk_length:
            filename = self._dump(self.chunks[-1])
            self.chunks[-1] = filename
            self.chunks.append([])

    def extend(self, value):
        for _ in value:
            self.append(_)

    def pop(self):
        if len(self.chunks[-1]) < 1:
            self.chunks.pop()
            try:
                with open(self.chunks[-1], "rb") as f:
                    self.chunks[-1] = pickle.loads(zlib.decompress(f.read()))
            except IOError, ex:
                errMsg = "exception occurred while retrieving data "
                errMsg += "from a temporary file ('%s')" % ex.message
                raise SqlmapSystemException, errMsg

        return self.chunks[-1].pop()

    def index(self, value):
        for index in xrange(len(self)):
            if self[index] == value:
                return index

        return ValueError, "%s is not in list" % value

    def _dump(self, chunk):
        try:
            handle, filename = tempfile.mkstemp(prefix=MKSTEMP_PREFIX.BIG_ARRAY)
            self.filenames.add(filename)
            os.close(handle)
            with open(filename, "w+b") as f:
                f.write(zlib.compress(pickle.dumps(chunk, pickle.HIGHEST_PROTOCOL), BIGARRAY_COMPRESS_LEVEL))
            return filename
        except (OSError, IOError), ex:
            errMsg = "exception occurred while storing data "
            errMsg += "to a temporary file ('%s'). Please " % ex.message
            errMsg += "make sure that there is enough disk space left. If problem persists, "
            errMsg += "try to set environment variable 'TEMP' to a location "
            errMsg += "writeable by the current user"
            raise SqlmapSystemException, errMsg

    def _checkcache(self, index):
        if (self.cache and self.cache.index != index and self.cache.dirty):
            filename = self._dump(self.cache.data)
            self.chunks[self.cache.index] = filename

        if not (self.cache and self.cache.index == index):
            try:
                with open(self.chunks[index], "rb") as f:
                    self.cache = Cache(index, pickle.loads(zlib.decompress(f.read())), False)
            except IOError, ex:
                errMsg = "exception occurred while retrieving data "
                errMsg += "from a temporary file ('%s')" % ex.message
                raise SqlmapSystemException, errMsg

    def __getstate__(self):
        return self.chunks, self.filenames

    def __setstate__(self, state):
        self.__init__()
        self.chunks, self.filenames = state

    def __getslice__(self, i, j):
        retval = BigArray()

        i = max(0, len(self) + i if i < 0 else i)
        j = min(len(self), len(self) + j if j < 0 else j)

        for _ in xrange(i, j):
            retval.append(self[_])

        return retval

    def __getitem__(self, y):
        if y < 0:
            y += len(self)

        index = y / self.chunk_length
        offset = y % self.chunk_length
        chunk = self.chunks[index]

        if isinstance(chunk, list):
            return chunk[offset]
        else:
            self._checkcache(index)
            return self.cache.data[offset]

    def __setitem__(self, y, value):
        index = y / self.chunk_length
        offset = y % self.chunk_length
        chunk = self.chunks[index]

        if isinstance(chunk, list):
            chunk[offset] = value
        else:
            self._checkcache(index)
            self.cache.data[offset] = value
            self.cache.dirty = True

    def __repr__(self):
        return "%s%s" % ("..." if len(self.chunks) > 1 else "", self.chunks[-1].__repr__())

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]

    def __len__(self):
        return len(self.chunks[-1]) if len(self.chunks) == 1 else (len(self.chunks) - 1) * self.chunk_length + len(self.chunks[-1])
