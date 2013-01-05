'''
dbms.py

Copyright 2013 Andres Riancho

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

import sys
import sqlite3

from functools import partial
from concurrent.futures import Future, Executor
from multiprocessing.dummy import Queue, Process

from core.data.misc.file_utils import replace_file_special_chars
from core.controllers.exceptions import DBException
from core.controllers.misc.temp_dir import get_temp_dir, create_temp_dir


class SQLiteDBMS(object):
    """
    Wrap sqlite connection in a way that allows concurrent requests from
    multiple threads.

    This is done by internally queuing the requests and processing them
    sequentially in a separate thread (in the same order they arrived).

    For all requests performed by the client, a Future [0] is returned, in
    other words, this is an asynchronous class.
    
    [0] http://www.python.org/dev/peps/pep-3148/
    """
    def __init__(self, filename, autocommit=False, journal_mode="OFF",
                 cache_size=2000):

        super(SQLiteDBMS, self).__init__()

        # Convert the filename to UTF-8, this is needed for windows, and special
        # characters, see:
        # http://www.sqlite.org/c3ref/open.html
        unicode_filename = filename.decode(sys.getfilesystemencoding())
        filename = unicode_filename.encode("utf-8")
        self.filename = replace_file_special_chars(filename)

        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.cache_size = cache_size

        self.sql_executor = sqex = SQLiteExecutor()
        sqlite3_connect = partial(sqex.submit_blocking, sqlite3.connect)
        
        #
        #    Setup phase
        #
        if self.autocommit:
            conn = sqlite3_connect(self.filename,
                                   isolation_level=None,
                                   check_same_thread=True)
        else:
            conn = sqlite3_connect(self.filename,
                                   check_same_thread=True)
        
        conn_execute = partial(sqex.submit_blocking, conn.execute)
        
        conn_execute('PRAGMA journal_mode = %s' % self.journal_mode)
        conn_execute('PRAGMA cache_size = %s' % self.cache_size)
        conn.text_factory = str
        
        self.cursor = sqex.submit_blocking(conn.cursor)
        
        cursor_execute = partial(sqex.submit_blocking, self.cursor.execute)
        cursor_execute('PRAGMA synchronous=OFF')
        
        # Store these attrs for later use, these are basically helpers to
        # write less code in the methods below
        self.cursor_execute_blocking = cursor_execute
        self.cursor_execute = partial(sqex.submit, self.cursor.execute)
        self.conn_commit = partial(sqex.submit, conn.commit)

    def execute(self, query, parameters=(), commit=False):
        """
        `execute` calls are non-blocking: just queue up the request and
        return a future.
        """
        fr = self.cursor_execute(query, parameters)
        
        if self.autocommit or commit:
            self.conn_commit()
            
        return fr

    def select(self, query, parameters=()):
        '''
        I can't think about any non-blocking use of calling select()
        '''
        ftor = self.sql_executor.submit_fetch_all
        return ftor(self.cursor.execute, query, parameters).result()

    def select_one(self, sql, parameters=()):
        """
        @return: Only the first row of the SELECT, or None if there are no
        matching rows.
        """
        try:
            return self.select(sql, parameters)[0]
        except IndexError:
            return None

    def commit(self):
        self.conn_commit()

    def close(self):
        self.conn_commit()
        self.sql_executor.stop()

    def get_file_name(self):
        '''Return DB filename.'''
        return self.filename
    
    def drop_table(self, name):
        sql = 'DROP TABLE %s' % name
        return self.execute(sql, commit=True)
    
    def create_table(self, name, columns, pk_columns=()):
        '''
        Create table in convenient way.
        '''
        if not name:
            raise ValueError('create_table requires a table name')
        
        if not columns:
            raise ValueError('create_table requires column names and types')
        
        # Create the table
        sql = 'CREATE TABLE %s (' % name
        
        all_columns = []
        for column_data in columns:
            column_name, column_type = column_data
            all_columns.append('%s %s' % (column_name, column_type))
            
        sql += ', '.join(all_columns)
        
        # Finally the PK
        if pk_columns:
            sql += ', PRIMARY KEY (%s)' % ','.join(pk_columns)

        sql += ')'

        return self.execute(sql, commit=True)

    def table_exists(self, name):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"\
                " LIMIT 1"
        r = self.select(query, (name,))
        return bool(r)        

    def create_index(self, table, columns):
        '''
        Create index for speed and performance

        @param table: The table from which you want to create an index from
        @param columns: A list of column names.
        '''
        sql = 'CREATE INDEX %s_index ON %s( %s )' % (
            table, table, ','.join(columns))

        return self.execute(sql, commit=True)


class SQLiteExecutor(Process):
    '''
    A very simple thread that takes work via submit() and processes it in a
    different thread.
    '''
    DEBUG = False
    
    def __init__(self):
        super(SQLiteExecutor, self).__init__()
        
        # Setting the thread to daemon mode so it dies with the rest of the
        # process, and a name so we can identify it during debugging sessions
        self.daemon = True
        self.name = 'SQLiteExecutor'
        
        self._in_queue = Queue()
        self.start()
    
    def submit(self, func, *args, **kwds):
        future = Future()
        self._in_queue.put((func, False, args, kwds, future) )
        return future

    def submit_fetch_all(self, func, *args, **kwds):
        future = Future()
        self._in_queue.put((func, True, args, kwds, future) )
        return future
    
    def submit_blocking(self, func, *args, **kwds):
        future = Future()
        self._in_queue.put((func, False, args, kwds, future))
        return future.result()

    def stop(self):
        self._in_queue.put(None)
    
    def run(self):
        '''
        This is the "main" method for this class, the one that
        consumes the commands which are sent to the Queue. The idea is to have
        the following architecture features:
            * Other parts of the framework which want to insert into the DB simply
              add an item to our input Queue and "forget about it" since it will
              be processed in another thread.

            * Only one thread accesses the sqlite3 object, which avoids many
            issues because of sqlite's non thread-safeness

        The Queue.get() will make sure we don't have 100% CPU usage in the loop
        '''
        while True:
            work_item = self._in_queue.get()
            
            if work_item is None:
                break
            else:
                func, fetch_all, args, kwargs, future = work_item
                
                if not future.set_running_or_notify_cancel():
                    return
                
                if self.DEBUG:
                    print func, args, kwargs
                    
                try:
                    result = func(*args, **kwargs)
                except Exception, e:
                    dbe = DBException(str(e))
                    future.set_exception(dbe)
                else:
                    # TODO: Is there a better way to do this? By doing this I'm
                    #       storing all results in memory
                    if fetch_all:
                        result = result.fetchall()

                    future.set_result(result)

create_temp_dir()
default_db = SQLiteDBMS('%s/main.db' % get_temp_dir())

def get_default_db_instance():
    return default_db
