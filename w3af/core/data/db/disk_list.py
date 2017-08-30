"""
DiskList.py

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
#magic
import __builtin__

import hashlib
import cPickle

from w3af.core.data.misc.cpickle_dumps import cpickle_dumps
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.db.dbms import get_default_temp_db_instance
from w3af.core.data.fuzzer.utils import rand_alpha

# Disk list states
OPEN = 1
CLOSED = 2


class DiskList(object):
    """
    A DiskList is a sqlite3 wrapper which has the following features:
        - Implements a list-like API
        - Stores all list items in a sqlite3 table
        - Is thread safe
        - Implements an iterator and a reversed iterator

    I had to replace the old DiskList because the old one did not support
    iteration, and the only way of adding iteration to that object was doing
    something like this:

    def __iter__(self):
        return self._shelve.keys()

    Which in most cases would be stupid, because it would have to retrieve all
    the values saved on disk to memory, and then perform iteration over that
    list. Another problem is that this iteration was performed tons of times,
    thus slowing down the whole process with many disk reads of tens and maybe
    hundreds of MB's.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, table_prefix=None):
        self.db = get_default_temp_db_instance()

        prefix = '' if table_prefix is None else ('%s_' % table_prefix)
        self.table_name = 'disk_list_' + prefix + rand_alpha(30)

        # Create table
        # DO NOT add the AUTOINCREMENT flag to the table creation since that
        # will break __getitem__ when an item is removed, see:
        #     http://www.sqlite.org/faq.html#q1
        columns = [('index_', 'INTEGER'),
                   ('eq_attrs', 'TEXT'),
                   ('pickle', 'BLOB')]
        pks = ['index_']
        
        self.db.create_table(self.table_name, columns, pks)
        self.db.create_index(self.table_name, ['eq_attrs'])
        self.db.commit()

        self._state = OPEN

    def cleanup(self):
        assert self._state == OPEN

        self.db.drop_table(self.table_name)
        self._state = CLOSED

    def _get_eq_attrs_values(self, obj):
        """
        :param obj: The object from which I need a hash.

        :return: A hash representing the eq_attrs specified in the DiskItem.
        """
        concatenated_eq_attrs = self.__internal_get_eq_attrs_values(obj)
        return hashlib.md5(concatenated_eq_attrs).hexdigest()

    def __internal_get_eq_attrs_values(self, obj):
        """
        :param obj: The object from which I need a unique string.

        :return: A string with all the values from the get_eq_attrs() method
                 concatenated. This should represent the object in an unique
                 way.
        """
        if type(obj).__name__ in dir(__builtin__):
            return cpickle_dumps(obj)

        elif obj is None:
            return cpickle_dumps(obj)

        elif isinstance(obj, DiskItem):
            result = ''
            
            for attr in obj.get_eq_attrs():
                value = getattr(obj, attr)
                result += self.__internal_get_eq_attrs_values(value)

            return result
        
        else:
            msg = ('Complex classes like %s need to inherit from DiskItem to'
                   ' be stored.')
            raise Exception(msg % type(obj))

    def __contains__(self, value):
        """
        :return: True if the value is in our list.
        """
        assert self._state == OPEN

        t = (self._get_eq_attrs_values(value),)
        # Adding the "limit 1" to the query makes it faster, as it won't
        # have to scan through all the table/index, it just stops on the
        # first match.
        query = 'SELECT count(*) FROM %s WHERE eq_attrs=? LIMIT 1' % self.table_name
        r = self.db.select_one(query, t)
        return bool(r[0])

    def append(self, value):
        """
        Append a value to the DiskList.

        :param value: The value to append.
        """
        assert self._state == OPEN
        pickled_obj = cpickle_dumps(value)
        eq_attrs = self._get_eq_attrs_values(value)
        t = (eq_attrs, pickled_obj)
        
        query = "INSERT INTO %s VALUES (NULL, ?, ?)" % self.table_name
        self.db.execute(query, t)

    def clear(self):
        assert self._state == OPEN
        self.db.execute("DELETE FROM %s WHERE 1=1" % self.table_name)

    def extend(self, value_list):
        """
        Extend the disk list with a group of items that is provided in
        @value_list

        :return: None
        """
        assert self._state == OPEN
        for value in value_list:
            self.append(value)

    def ordered_iter(self):
        assert self._state == OPEN

        # TODO: How do I make the __iter__ thread safe?
        # How do I avoid loading all items in memory?
        objects = []
        results = self.db.select('SELECT pickle FROM %s' % self.table_name)

        for r in results:
            obj = cPickle.loads(r[0])
            objects.append(obj)
        
        for obj in sorted(objects):
            yield obj

    def __iter__(self):
        assert self._state == OPEN

        # TODO: How do I make the __iter__ thread safe?
        results = self.db.select('SELECT pickle FROM %s' % self.table_name)
        for r in results:
            obj = cPickle.loads(r[0])
            yield obj

    def __reversed__(self):
        assert self._state == OPEN

        # TODO: How do I make the __iter__ thread safe?
        query = 'SELECT pickle FROM %s ORDER BY index_ DESC'
        results = self.db.select(query % self.table_name)
        for r in results:
            obj = cPickle.loads(r[0])
            yield obj

    def __getitem__(self, key):
        assert self._state == OPEN

        if isinstance(key, slice):
            return self._slice_list(key)
        
        # I need to add 1 to this key because the autoincrement in SQLITE
        # starts counting from 1 instead of 0
        if key >= 0:
            index_ = int(key) + 1
        else:
            # TODO: There's room for improvement in this code since we could
            # find a way to avoid the len(self) which generated one more SELECT
            # statement and is not very nice in terms of performance
            index_ = len(self) + int(key) + 1
            
        query = 'SELECT pickle FROM %s WHERE index_ = ?' % self.table_name
        try:
            r = self.db.select_one(query, (index_,))
            obj = cPickle.loads(r[0])
        except:
            raise IndexError('list index out of range')
        else:
            return obj
    
    def _slice_list(self, slice_inst):
        assert self._state == OPEN

        start = slice_inst.start or 0
        stop = slice_inst.stop or len(self)
        step = slice_inst.step or 1
        
        copy = DiskList()
        disk_list_length = len(self)

        # TODO: This piece of code is VERY SLOW and can be improved. Please
        # note that for each element that's selected by the xrange/step, we'll
        # SELECT on the original list and INSERT on the copy.
        #
        # We could find ways to make this in only one SELECT/INSERT, but the
        # main problem is when I add, remove, and then try to slice a DiskList
        for i in xrange(start, stop, step):
            if i >= disk_list_length:
                break
            copy.append(self[i])

        return copy
            
    def __len__(self):
        assert self._state == OPEN

        query = 'SELECT count(*) FROM %s' % self.table_name
        r = self.db.select_one(query)
        return r[0]

    def __unicode__(self):
        return u'<DiskList [%s]>' % ', '.join([unicode(i) for i in self])
    
    __str__ = __unicode__

