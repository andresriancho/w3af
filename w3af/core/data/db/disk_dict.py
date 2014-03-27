"""
disk_dict.py

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
import cPickle

from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.db.dbms import get_default_temp_db_instance


class DiskDict(object):
    """
    It's a dict that stores items in a sqlite3 database and has the following
    features:
        - Dict-like API
        - Is thread safe
        - Deletes the table when the instance object is deleted

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        self.db = get_default_temp_db_instance()

        self.table_name = rand_alpha(30)

        # Create table
        # DO NOT add the AUTOINCREMENT flag to the table creation since that
        # will break __getitem__ when an item is removed, see:
        #     http://www.sqlite.org/faq.html#q1
        columns = [('index_', 'INTEGER'),
                   ('key', 'BLOB'),
                   ('value', 'BLOB')]
        pks = ['index_']
        
        self.db.create_table(self.table_name, columns, pks)
        self.db.create_index(self.table_name, ['key'])
        self.db.commit()

    def cleanup(self):
        self.db.drop_table(self.table_name)

    def keys(self):
        pickled_keys = self.db.select('SELECT key FROM %s' % self.table_name)
        result_list = [] 
        
        for r in pickled_keys:
            result_list.append(cPickle.loads(r[0]))
        
        return result_list

    def iterkeys(self):
        pickled_keys = self.db.select('SELECT key FROM %s' % self.table_name)
        
        for r in pickled_keys:
            yield cPickle.loads(r[0])

    def __contains__(self, key):
        """
        :return: True if the value is in keys
        """
        # Adding the "limit 1" to the query makes it faster, as it won't
        # have to scan through all the table/index, it just stops on the
        # first match.
        query = 'SELECT count(*) FROM %s WHERE key=? limit 1' % self.table_name
        r = self.db.select_one(query, (cPickle.dumps(key),))
        return bool(r[0])
    
    def __setitem__(self, key, value):
        # Test if it is already in the DB:
        if key in self:
            query = 'UPDATE %s SET value = ? WHERE key=?' % self.table_name
            self.db.execute(query, (cPickle.dumps(value), cPickle.dumps(key)))
        else:
            query = "INSERT INTO %s VALUES (NULL, ?, ?)" % self.table_name
            self.db.execute(query, (cPickle.dumps(key), cPickle.dumps(value)))

    def __getitem__(self, key):
        query = 'SELECT value FROM %s WHERE key=? limit 1' % self.table_name
        r = self.db.select(query, (cPickle.dumps(key),))
        
        if not r:
            raise KeyError('%s not in DiskDict.' % key)

        return cPickle.loads(r[0][0])

    def __len__(self):
        query = 'SELECT count(*) FROM %s' % self.table_name
        r = self.db.select_one(query)
        return r[0]

    def get(self, key, default=-456):
        if key in self:
            return self[key]

        if default is not -456:
            return default

        raise KeyError()
