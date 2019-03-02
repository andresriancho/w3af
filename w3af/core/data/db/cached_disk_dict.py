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
        self._access_count = dict()

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
        items = self._access_count.items()
        items.sort(sort_by_value)

        iterator = min(self._max_in_memory, len(items))

        for i in xrange(iterator):
            yield items[i][0]

    def _belongs_in_memory(self, key):
        """
        :param key: A key
        :return: True if the key should be stored in memory
        """
        if key in self._get_keys_for_memory():
            return True

        return False

    def _increase_access_count(self, key):
        access_count = self._access_count.get(key, 0)
        access_count += 1
        self._access_count[key] = access_count

        self._move_key_to_disk_if_needed(key)
        self._move_key_to_memory_if_needed(key)

    def _move_key_to_disk_if_needed(self, key):
        """
        Analyzes the current access count for the last accessed key and
        checks if any if the keys in memory should be moved to disk.

        :param key: The key that was last accessed
        :return: The name of the key that was moved to disk, or None if
                 all the keys are still in memory.
        """
        for key in self._in_memory.keys():
            if not self._belongs_in_memory(key):
                try:
                    value = self._in_memory[key]
                except KeyError:
                    return None
                else:
                    self._disk_dict[key] = value
                    self._in_memory.pop(key, None)
                    return key

    def _move_key_to_memory_if_needed(self, key):
        """
        Analyzes the current access count for the last accessed key and
        checks if any if the keys in disk should be moved to memory.

        :param key: The key that was last accessed
        :return: The name of the key that was moved to memory, or None if
                 all the keys are still on disk.
        """
        key_belongs_in_memory = self._belongs_in_memory(key)

        if not key_belongs_in_memory:
            return None

        try:
            value = self._disk_dict[key]
        except KeyError:
            return None
        else:
            self._in_memory[key] = value
            self._disk_dict.pop(key, None)
            return key

    def __setitem__(self, key, value):
        if len(self._in_memory) < self._max_in_memory:
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


def sort_by_value(a, b):
    return cmp(b[1], a[1])
