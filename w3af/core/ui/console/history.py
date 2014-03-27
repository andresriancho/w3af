"""
history.py

Copyright 2008 Andres Riancho

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
import copy


class historyTable(object):
    """
    A wrapper around a dictionary which stores menu-related history objects.
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """
    def __init__(self):
        self._table = {}

    def get_history(self, key):
        """
        Returns a history object for the key (which is a menu name).
        If no object exist yet, a new one is created and registered.
        :param key
        """
        if key in self._table:
            result = self._table[key]
        else:
            result = history()
            self._table[key] = result

        return result


class history(object):
    """
    Remembers the commands which were executed and allows navigate in that list.
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)

    """

    def __init__(self):
        self._stack = []
        self._pointer = 0
        self._pending = None

    def remember(self, pending):
        self._stack.append(copy.deepcopy(pending))
        self._pointer = len(self._stack)

    def back(self, pending=None):
        if self._pointer == 0:
            return None

        if self._pointer == len(self._stack):
            self._pending = pending

        self._pointer -= 1
        return self._stack[self._pointer]

    def forward(self):

        sl = len(self._stack)
        if self._pointer == sl:
            return None

        self._pointer += 1

        if self._pointer == sl:
            if self._pending is not None:
                result = self._pending
                self._pending = None
            else:
                result = None
        else:
            result = self._stack[self._pointer]

        return result
