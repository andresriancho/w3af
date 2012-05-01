'''
disk_list.py

Copyright 2008 Andres Riancho

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

from itertools import repeat, starmap 
from random import choice
import os
import sqlite3
import string
import sys
import threading
import cPickle

from core.controllers.misc.temp_dir import get_temp_dir
from core.data.db.disk_item import disk_item


class disk_list(object):
    '''
    A disk_list is a sqlite3 wrapper which has the following features:
        - Automagically creates the file in the /tmp directory
        - Is thread safe
        - Implements an iterator and a reversed iterator
        - Deletes the file when the disk_list object is deleted from memory
    
    I had to replace the old disk_list because the old one did not support
    iteration, and the only way of adding iteration to that object was doing
    something like this:
    
    def __iter__(self):
        return self._shelve.keys()
        
    Which in most cases would be stupid, because it would have to retrieve all
    the values saved on disk to memory, and then perform iteration over that
    list. Another problem is that this iteration was performed tons of times,
    thus slowing down the whole process with many disk reads of tens and maybe
    hundreds of MB's.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        '''
        Create the sqlite3 database and the thread lock.
        
        @param text_factory: A callable object to handle strings.
        '''
        # Init some attributes
        self._conn = None
        self._filename = None
        self._current_index = 0

        # Create the lock
        self._db_lock = threading.RLock()
        
        fail_count = 0
        while True:
            # Get the temp filename to use
            tempdir = get_temp_dir()
            # A 12-chars random string
            fn = ''.join(starmap(choice, repeat((string.letters,), 12)))
            self._filename = os.path.join(tempdir, fn + '.w3af.temp_db')
            
            if sys.platform in ('win32', 'cygwin'):
                self._filename = self._filename.decode("MBCS").encode("utf-8")

            try:
                # Create the database
                self._conn = sqlite3.connect(self._filename,
                                             check_same_thread=False)
                self._conn.text_factory = str
                
                # Modify some default values
                # http://www.sqlite.org/pragma.html#pragma_cache_size (default: 2000)
                # less pages in memory
                self._conn.execute('PRAGMA cache_size = 200')
                # http://www.sqlite.org/pragma.html#pragma_synchronous (default: 1)
                # sends data to OS and does NOT wait for it to be on-disk
                self._conn.execute('PRAGMA synchronous = 0')
                # http://www.sqlite.org/pragma.html#pragma_synchronous
                # disables journal -> ROLLBACK
                self._conn.execute('PRAGMA journal_mode = OFF')
                 
                # Create table
                self._conn.execute(
                    '''CREATE TABLE data (index_ REAL PRIMARY KEY, eq_attrs BLOB, pickle BLOB)''')

                # Create index
                self._conn.execute(
                    '''CREATE INDEX data_index ON data(eq_attrs)''')
                
            except Exception, e:
                
                fail_count += 1
                if fail_count == 5:
                    raise Exception('Failed to create database file. '
                        'Original exception: "%s %s"' % (e, self._filename))

                self._filename = None

            else:
                break
                
            # Now we perform a small trick... we remove the temp file directory
            # entry
            #
            # According to the python documentation: On Windows, attempting to
            # remove a file that is in use causes an exception to be raised;
            # on Unix, the directory entry is removed but the storage allocated
            # to the file is not made available until the original file is no
            # longer in use
            try:
                os.remove(self._filename)
            except Exception:
                pass
    
    def __del__(self):
        try:
            with self._db_lock:
                try:
                    self._conn.close()
                    os.remove(self._filename)
                except:
                    pass
        except:
            pass
    
    def _get_eq_attrs_values(self, obj):
        '''
        @param obj: The object from which I need a unique string.
        
        @return: A string with all the values from the get_eq_attrs() method
                 concatenated. This should represent the object in an unique
                 way. 
        '''
        result = ''
        
        if isinstance(obj, basestring):
            return obj
        
        elif isinstance(obj, (int, float)):
            return str(obj)
        
        elif isinstance(obj, (list, tuple, set)):
            for sub_obj in obj:
                result += self._get_eq_attrs_values(sub_obj)
            return result
        
        elif isinstance(obj, dict):
            for key, value in obj.iteritems():
                result += self._get_eq_attrs_values(key)
                result += self._get_eq_attrs_values(value)
            return result
           
        elif isinstance(obj, disk_item):        
            for attr in obj.get_eq_attrs():
                value = getattr(obj, attr)
                result += self._get_eq_attrs_values(value)
            
            return result
        else:
            msg = 'Complex classes like %s need to inherit from disk_item to be stored.'
            raise Exception(msg % type(obj))
    
    def __contains__(self, value):
        '''
        @return: True if the value is in our list.
        '''
        with self._db_lock:
            t = (self._get_eq_attrs_values(value),)
            # Adding the "limit 1" to the query makes it faster, as it won't 
            # have to scan through all the table/index, it just stops on the
            # first match.
            cursor = self._conn.execute(
                    'SELECT count(*) FROM data WHERE eq_attrs=? limit 1', t)
            return cursor.fetchone()[0]
    
    def append(self, value):
        '''
        Append a value to the disk_list.
        
        @param value: The value to append. 
        '''
        # thread safe here!
        with self._db_lock:
            pickled_obj = cPickle.dumps(value)
            eq_attrs = self._get_eq_attrs_values(value)
            t = (self._current_index, eq_attrs, pickled_obj)
            self._conn.execute("INSERT INTO data VALUES (?, ?, ?)", t)
            self._current_index += 1
    
    def clear(self):
        # thread safe here!
        with self._db_lock:
            self._conn.execute("DELETE FROM data WHERE 1=1")
            self._current_index = 0
    
    def extend(self, value_list):
        '''
        Extend the disk list with a group of items that is provided in @value_list
        
        @return: None
        '''
        for value in value_list:
            self.append(value)
    
    def ordered_iter(self):
        # TODO: How do I make the __iter__ thread safe?        
        cursor = self._conn.execute('SELECT pickle FROM data ORDER BY eq_attrs ASC')
        for r in cursor:
            obj = cPickle.loads(r[0])
            yield obj        
    
    def __iter__(self):
        # TODO: How do I make the __iter__ thread safe?        
        cursor = self._conn.execute('SELECT pickle FROM data')
        for r in cursor:
            obj = cPickle.loads(r[0])
            yield obj

    def __reversed__(self):
        # TODO: How do I make the __iter__ thread safe?        
        cursor = self._conn.execute('SELECT pickle FROM data ORDER BY index_ DESC')
        for r in cursor:
            obj = cPickle.loads(r[0])
            yield obj

    def __getitem__(self, key):
        try:
            cursor = self._conn.execute( 'SELECT pickle FROM data WHERE index_ = ?', (key,) )
            r = cursor.next()
            obj = cPickle.loads( r[0] )
        except:
            raise IndexError('list index out of range')
        else:
            return obj
        
    def __len__(self):
        with self._db_lock:
            cursor = self._conn.execute('SELECT count(*) FROM data')
            return cursor.fetchone()[0]

