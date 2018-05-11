"""
DiskSet.py

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
import threading

from w3af.core.data.db.disk_list import DiskList


class DiskSet(DiskList):
    """
    A DiskList that only allows to add/append unique items.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, table_prefix=None):
        super(DiskSet, self).__init__(table_prefix=table_prefix)

        self.lock = threading.RLock()
    
    def add(self, value):
        """
        Append a value to the DiskSet (only if the value is not already
        contained in this instance).

        :param value: The value to append.
        :return: True if the value was added. False if it existed and was not
                 added.
        """
        with self.lock:
            if self.__contains__(value):
                return False
            else:
                super(DiskSet, self).append(value)
                return True

    def update(self, value_list):
        """
        Extend the disk set with a list of items that is provided in @value_list

        :return: None
        """
        with self.lock:
            for value in value_list:
                self.add(value)

    def extend(self, *args):
        raise RuntimeError('Not a valid DiskSet method.')

    def append(self, *args):
        raise RuntimeError('Not a valid DiskSet method.')

    def __unicode__(self):
        return u'<DiskSet [%s]>' % ', '.join([unicode(i) for i in self])
    
    __str__ = __unicode__
