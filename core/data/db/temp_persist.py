'''
temp_persist.py

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

from __future__ import with_statement
from random import choice
import os
import sqlite3
import string
import sys
import threading

from core.controllers.misc.temp_dir import get_temp_dir

class disk_list(object):
    '''
    A disk_list is a sqlite3 wrapper which has the following features:
        - Automagically creates the file in the /tmp directory
        - Is thread safe
        - **NEW** Allows the usage of "for ... in" by the means of an iterator object.
        - Deletes the file when the temp_shelve object is deleted
    
    I had to replace the old disk_list because the old one did not support iteration, and the
    only way of adding iteration to that object was doing something like this:
    
    def __iter__(self):
        return self._shelve.keys()
        
    Which in most cases would be stupid, because it would have to retrieve all the values
    saved on disk to memory, and then perform iteration over that list. Another problem is that
    this iteration was performed tons of times, thus slowing down the whole process with many
    disk reads of tens and maybe hundreds of MB's.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, text_factory=sqlite3.OptimizedUnicode):
        '''
        Create the sqlite3 database and the thread lock.
        
        @param text_factory: A callable object to handle strings.
        '''
        # Init some attributes
        self._conn = None
        self._filename = None
        self._current_index = 0
        
        # text factory for the connection
        self._text_factory = text_factory

        # Create the lock
        self._db_lock = threading.RLock()
        
        fail_count = 0
        while True:
            # Get the temp filename to use
            tempdir = get_temp_dir()
            filename = ''.join([choice(string.letters) for i in range(12)]) + '.w3af.temp_db'
            self._filename = os.path.join(tempdir, filename)
            
            if sys.platform in ('win32', 'cygwin'):
                self._filename = self._filename.decode("MBCS").encode("utf-8")

            try:
                # Create the database
                self._conn = sqlite3.connect(self._filename, check_same_thread=False)
                
                # Set up the text_factory to the connection
                self._conn.text_factory = self._text_factory

                # Create table
                self._conn.execute(
                    '''CREATE TABLE data (index_ real, information text)''')

                # Create index
                self._conn.execute(
                    '''CREATE INDEX data_index ON data(information)''')

            except Exception,  e:
                
                fail_count += 1
                if fail_count == 5:
                    raise Exception('Failed to create database file. '
                        'Original exception: "%s %s"' % (e, self._filename))

                self._filename = None

            else:
                break
                
            # Now we perform a small trick... we remove the temp file directory entry
            #
            # According to the python documentation: On Windows, attempting to remove a file that
            # is in use causes an exception to be raised; on Unix, the directory entry is removed
            # but the storage allocated to the file is not made available until the original file
            # is no longer in use
            try:
                os.remove(self._filename)
            except Exception:
                pass
    
    def __del__(self):
        with self._db_lock:
            try:
                self._conn.close()
                os.remove(self._filename)
            except:
                pass
    
    def __contains__(self, value):
        '''
        @return: True if the str(value) is in our list.
        '''
        with self._db_lock:
            t = (str(value), )
            # Adding the "limit 1" to the query makes it faster, as it won't 
            # have to scan through all the table/index, it just stops on the
            # first match.
            cursor = self._conn.execute(
                    'SELECT count(*) FROM data WHERE information=? limit 1', t)
            return cursor.fetchone()[0]
    
    def append(self, value):
        '''
        Append a value to the disk_list.
        
        @param value: The value to append. In all cases we're going to store the str()
        representation of the value. In order to be consistent, in __contains__ we also
        perform a str(). 
        '''
        # thread safe here!
        with self._db_lock:
            t = (self._current_index, str(value))
            self._conn.execute("INSERT INTO data VALUES (?, ?)", t)
            self._current_index += 1
    
    def __iter__(self):
        #   TODO: How do I make the __iter__ thread safe?
        class my_cursor:
            def __init__(self, cursor):
                self._cursor = cursor
            
            def next(self):
                r = self._cursor.next()
                return r[0]
        
        cursor = self._conn.execute('SELECT information FROM data')
        mc = my_cursor(cursor)
        return mc
        
    def __len__(self):
        with self._db_lock:
            cursor = self._conn.execute('SELECT count(*) FROM data')
            return cursor.fetchone()[0]

import unittest
class disk_list_test(unittest.TestCase):

    def setUp(self):
        global get_temp_dir
        def get_temp_dir():
            return '/tmp/'

    def test_string_add_contains(self):
        dl = disk_list()
        for i in xrange(5000):
            r = self.create_string()
            dl.append( r )
        self.assertTrue( len(dl) == 5000 )
        self.assertTrue( r in dl )
        self.assertTrue( 'abc' not in dl )

    def test_string_add_contains(self):
        dl = disk_list()
        for i in xrange(5000):
            dl.append( i )
        self.assertTrue( len(dl) == 5000 )
        self.assertTrue( 500 in dl )        
        self.assertTrue( False not in dl )
        self.assertTrue( 'abc' not in dl )
        
        # TODO: This is not very nice... but for now we can bare with it.
        self.assertTrue( '500' in dl )

    def create_string():
        strr = ''
        for i in xrange(300):
            strr += choice(string.letters)
        return strr

