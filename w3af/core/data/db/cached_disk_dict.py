"""
cached_disk_dict.py

Copyright 2018 Andres Riancho

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
from collections import Counter

from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.fuzzer.utils import rand_alpha


class CachedDiskDict(object):
    """
    This data structure keeps the `max_in_memory` most frequently accessed
    keys in memory and stores the rest on disk.

    It is ideal for situations where a DiskDict is frequently accessed,
    fast read / writes are required, and items can take considerable amounts
    of memory.
    """
    def __init__(self, max_in_memory=50, table_prefix=None):
        """
        :param max_in_memory: The max number of items to keep in memory
        """
        assert max_in_memory > 0, 'In-memory items must be > 0'

        table_prefix = self._get_table_prefix(table_prefix)

        self._max_in_memory = max_in_memory
        self._disk_dict = DiskDict(table_prefix=table_prefix)
        self._in_memory = dict()
        self._access_count = Counter()

    def cleanup(self):
        self._disk_dict.cleanup()

    def _get_table_prefix(self, table_prefix):
        if table_prefix is None:
            table_prefix = 'cached_disk_dict_%s' % rand_alpha(16)
        else:
            args = (table_prefix, rand_alpha(16))
            table_prefix = 'cached_disk_dict_%s_%s' % args

        return table_prefix

    def get(self, key, default=-456):
        try:
            return self[key]
        except KeyError:
            if default is not -456:
                return default

        raise KeyError()

    def __getitem__(self, key):
        try:
            value = self._in_memory[key]
        except KeyError:
            # This will raise KeyError if k is not found, and that is OK
            # because we don't need to increase the access count when the
            # key doesn't exist
            value = self._disk_dict[key]

        self._increase_access_count(key)
        return value

    def _get_keys_for_memory(self):
        """
        :return: Generate the names of the keys that should be kept in memory.
                 For example, if `max_in_memory` is set to 2 and:

                    _in_memory: {1: None, 2: None}
                    _access_count: {1: 10, 2: 20, 3: 5}
                    _disk_dict: {3: None}

                Then the method will generate [1, 2].
        """
        return [k for k, v in self._access_count.most_common(self._max_in_memory)]

    def _increase_access_count(self, key):
        self._access_count.update([key])

        keys_for_memory = self._get_keys_for_memory()

        self._move_key_to_disk_if_needed(keys_for_memory)
        self._move_key_to_memory_if_needed(key, keys_for_memory)

    def _move_key_to_disk_if_needed(self, keys_for_memory):
        """
        Analyzes the current access count for the last accessed key and
        checks if any if the keys in memory should be moved to disk.

        :param keys_for_memory: The keys that should be in memory
        :return: The name of the key that was moved to disk, or None if
                 all the keys are still in memory.
        """
        for key in self._in_memory:

            if key in keys_for_memory:
                continue

            try:
                value = self._in_memory.pop(key)
            except KeyError:
                return
            else:
                self._disk_dict[key] = value
                return key

    def _move_key_to_memory_if_needed(self, key, keys_for_memory):
        """
        Analyzes the current access count for the last accessed key and
        checks if any if the keys in disk should be moved to memory.

        :param key: The key that was last accessed
        :param keys_for_memory: The keys that should be in memory
        :return: The name of the key that was moved to memory, or None if
                 all the keys are still on disk.
        """
        # The key is already in memory, nothing to do here
        if key in self._in_memory:
            return

        # The key must not be in memory, nothing to do here
        if key not in keys_for_memory:
            return

        try:
            value = self._disk_dict.pop(key)
        except KeyError:
            return
        else:
            self._in_memory[key] = value
            return key

    def __setitem__(self, key, value):
        if key in self._in_memory:
            self._in_memory[key] = value

        elif len(self._in_memory) < self._max_in_memory:
            self._in_memory[key] = value

        else:
            self._disk_dict[key] = value

        self._increase_access_count(key)

    def __delitem__(self, key):
        try:
            del self._in_memory[key]
        except KeyError:
            # This will raise KeyError if k is not found, and that is OK
            # because we don't need to increase the access count when the
            # key doesn't exist
            del self._disk_dict[key]

        try:
            del self._access_count[key]
        except KeyError:
            # Another thread removed this key
            pass

    def __contains__(self, key):
        if key in self._in_memory:
            self._increase_access_count(key)
            return True

        if key in self._disk_dict:
            self._increase_access_count(key)
            return True

        return False

    def __iter__(self):
        """
        Decided not to increase the access count when iterating through the
        items. In most cases the iteration will be performed on all items,
        thus increasing the access count +1 for each, which will leave all
        access counts +1, forcing no movements between memory and disk.
        """
        for key in self._in_memory:
            yield key

        for key in self._disk_dict:
            yield key

    def iteritems(self):
        for key, value in self._in_memory.iteritems():
            yield key, value

        for key, value in self._disk_dict.iteritems():
            yield key, value
