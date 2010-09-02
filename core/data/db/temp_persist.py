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
import sqlite3

import threading
import os
import sys

from random import choice
import string

try:
   import cPickle as pickle
except:
   import pickle

try:
    from core.controllers.misc.temp_dir import get_temp_dir
except:
    def get_temp_dir():
        return '/tmp/'


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
    
    def __init__(self):
        '''
        Create the sqlite3 database and the thread lock.
        
        @return: None
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
            filename = ''.join([choice(string.letters) for i in range(12)]) + '.w3af.temp_db'
            self._filename = os.path.join(tempdir, filename)
            
            # https://sourceforge.net/tracker/?func=detail&aid=2828136&group_id=170274&atid=853652
            if (sys.platform=='win32') or (sys.platform=='cygwin'):
                self._filename = self._filename.decode( "MBCS" ).encode("utf-8" )

            try:
                # Create the database
                self._conn = sqlite3.connect(self._filename, check_same_thread=False)
                self._conn.text_factory = str
                # Create table
                self._conn.execute('''create table data (index_ real, information text)''')

            except Exception,  e:
                self._filename = None
                
                fail_count += 1
                if fail_count == 5:
                    raise Exception('Failed to create databse file. Original exception: ' + str(e))
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
        with self._db_lock:
            t = (value, )
            cursor = self._conn.execute('select count(*) from data where information=?', t)
            return cursor.fetchone()[0]
    
    def append(self, value):
        # thread safe here!
        with self._db_lock:
            t = (self._current_index, value)
            self._conn.execute("insert into data values (?, ?)", t)
            self._current_index += 1
    
    def __iter__(self):
        #   TODO: How do I make the __iter__ thread safe?
        class my_cursor:
            def __init__(self, cursor):
                self._cursor = cursor
            
            def next(self):
                r = self._cursor.next()
                return r[0]
        
        cursor = self._conn.execute('select information from data')
        mc = my_cursor(cursor)
        return mc
        
    def __len__(self):
        with self._db_lock:
            cursor = self._conn.execute('select count(*) from data')
            return cursor.fetchone()[0]
        
if __name__ == '__main__':
    def create_string():
        strr = ''
        for i in xrange(300):
            strr += choice(string.letters)
        return strr
    
    print ''
    print 'Testing disk_list:'
    dlist = disk_list()
    
    print '1- Loading items...'
    for i in xrange(5000):
        r = create_string()
        dlist.append( r )
    
    print '2- Assert statements...'
    assert len(dlist) == 5000
    assert r in dlist
    assert not 'abc' in dlist
    print 'Done!'
