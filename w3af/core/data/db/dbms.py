"""
dbms.py

Copyright 2013 Andres Riancho

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
from __future__ import with_statement

import sys
import os
import sqlite3

from functools import wraps

from concurrent.futures import Future
from multiprocessing.dummy import Queue, Process

from w3af.core.data.misc.file_utils import replace_file_special_chars
from w3af.core.controllers.exceptions import DBException
from w3af.core.controllers.misc.temp_dir import get_temp_dir, create_temp_dir

# Constants
SETUP = 'SETUP'
QUERY = 'QUERY'
SELECT = 'SELECT'
COMMIT = 'COMMIT'
POISON = 'POISON'


def verify_started(meth):
    
    @wraps(meth)
    def inner_verify_started(self, *args, **kwds):
        msg = 'No calls to SQLiteDBMS can be made after stop().'
        assert self.sql_executor.is_alive(), msg
        return meth(self, *args, **kwds)
    
    return inner_verify_started


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
        
        in_queue = Queue()
        self.sql_executor = SQLiteExecutor(in_queue)
        self.sql_executor.start()
        
        #
        #    Performs sqlite database setup, this has the nice side-effect
        #    that .result() will block until the thread is started and
        #    processing tasks.
        #
        future = self.sql_executor.setup(filename, autocommit, journal_mode,
                                         cache_size)
        # Raises an exception if an error was found during setup
        future.result()
        
        self.filename = filename
        self.autocommit = autocommit
    
    @verify_started
    def execute(self, query, parameters=(), commit=False):
        """
        `execute` calls are non-blocking: just queue up the request and
        return a future.
        """
        fr = self.sql_executor.query(query, parameters)
        
        if self.autocommit or commit:
            self.sql_executor.commit()
            
        return fr

    @verify_started
    def select(self, query, parameters=()):
        """
        I can't think about any non-blocking use of calling select()
        """
        future = self.sql_executor.select(query, parameters)
        return future.result()

    @verify_started
    def select_one(self, query, parameters=()):
        """
        :return: Only the first row of the SELECT, or None if there are no
        matching rows.
        """
        try:
            return self.select(query, parameters)[0]
        except IndexError:
            return None

    @verify_started
    def commit(self):
        self.sql_executor.commit()

    @verify_started
    def close(self):
        self.commit()
        self.sql_executor.stop()

    def get_file_name(self):
        """Return DB filename."""
        return self.filename
    
    def drop_table(self, name):
        query = 'DROP TABLE %s' % name
        return self.execute(query, commit=True)
    
    def clear_table(self, name):
        """
        Remove all rows from a table.
        """
        query = 'DELETE FROM %s WHERE 1=1' % name
        return self.execute(query, commit=True)
    
    def create_table(self, name, columns, pk_columns=()):
        """
        Create table in convenient way.
        """
        if not name:
            raise ValueError('create_table requires a table name')
        
        if not columns:
            raise ValueError('create_table requires column names and types')
        
        # Create the table
        query = 'CREATE TABLE %s (' % name
        
        all_columns = []
        for column_data in columns:
            column_name, column_type = column_data
            all_columns.append('%s %s' % (column_name, column_type))
            
        query += ', '.join(all_columns)
        
        # Finally the PK
        if pk_columns:
            query += ', PRIMARY KEY (%s)' % ','.join(pk_columns)

        query += ')'

        return self.execute(query, commit=True)

    def table_exists(self, name):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"\
                " LIMIT 1"
        r = self.select(query, (name,))
        return bool(r)        

    def create_index(self, table, columns):
        """
        Create index for speed and performance

        :param table: The table from which you want to create an index from
        :param columns: A list of column names.
        """
        query = 'CREATE INDEX %s_index ON %s( %s )' % (table, table,
                                                       ','.join(columns))

        return self.execute(query, commit=True)


class SQLiteExecutor(Process):
    """
    A very simple thread that takes work via submit() and processes it in a
    different thread.
    """
    DEBUG = False
    
    def __init__(self, in_queue):
        super(SQLiteExecutor, self).__init__(name='SQLiteExecutor')
        
        # Setting the thread to daemon mode so it dies with the rest of the
        # process, and a name so we can identify it during debugging sessions
        self.daemon = True
        self.name = 'SQLiteExecutor'
        
        self._in_queue = in_queue

    def query(self, query, parameters):
        future = Future()
        request = (QUERY, (query, parameters), {}, future)
        self._in_queue.put(request)
        return future
    
    def _query_handler(self, query, parameters):
        return self.cursor.execute(query, parameters)

    def select(self, query, parameters):
        future = Future()
        request = (SELECT, (query, parameters), {}, future)
        self._in_queue.put(request)
        return future
    
    def _select_handler(self, query, parameters):
        result = self.cursor.execute(query, parameters)
        result_lst = []
        for row in result:
            result_lst.append(row)
        return result_lst
    
    def commit(self):
        future = Future()
        request = (COMMIT, None, None, future)
        self._in_queue.put(request)
        return future

    def _commit_handler(self):
        return self.conn.commit()
        
    def stop(self):
        future = Future()
        request = (POISON, None, None, future)
        self._in_queue.put(request)
        return future
    
    def setup(self, filename, autocommit=False, journal_mode="OFF",
              cache_size=2000):
        """
        Request the process to perform a setup.
        """
        future = Future()
        request = (SETUP,
                   (filename,),
                   {'autocommit': autocommit,
                    'journal_mode': journal_mode,
                    'cache_size': autocommit},
                   future)
        self._in_queue.put(request)
        return future
    
    def _setup_handler(self, filename, autocommit=False, journal_mode="OFF",
                         cache_size=2000):
        # Convert the filename to UTF-8, this is needed for windows, and special
        # characters, see:
        # http://www.sqlite.org/c3ref/open.html
        unicode_filename = filename.decode(sys.getfilesystemencoding())
        filename = unicode_filename.encode("utf-8")
        self.filename = replace_file_special_chars(filename)

        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.cache_size = cache_size
        
        #
        #    Setup phase
        #
        if self.autocommit:
            conn = sqlite3.connect(self.filename,
                                   isolation_level=None,
                                   check_same_thread=True)
        else:
            conn = sqlite3.connect(self.filename,
                                   check_same_thread=True)
        
        conn.execute('PRAGMA journal_mode = %s' % self.journal_mode)
        conn.execute('PRAGMA cache_size = %s' % self.cache_size)
        conn.text_factory = str
        self.conn = conn
        
        self.cursor = conn.cursor()
        self.cursor.execute('PRAGMA synchronous=OFF')
    
    def run(self):
        """
        This is the "main" method for this class, the one that
        consumes the commands which are sent to the Queue. The idea is to have
        the following architecture features:
            * Other parts of the framework which want to insert into the DB simply
              add an item to our input Queue and "forget about it" since it will
              be processed in another thread.

            * Only one thread accesses the sqlite3 object, which avoids many
            issues because of sqlite's non thread-safeness

        The Queue.get() will make sure we don't have 100% CPU usage in the loop
        """
        OP_CODES = {SETUP: self._setup_handler,
                    QUERY: self._query_handler,
                    SELECT: self._select_handler,
                    COMMIT: self._commit_handler,
                    POISON: POISON}
        
        while True:
            op_code, args, kwds, future = self._in_queue.get()
            
            args = args or ()
            kwds = kwds or {}
            
            if self.DEBUG:
                print '%s %s %s' % (op_code, args, kwds)
            
            handler = OP_CODES.get(op_code, None)
            
            if handler is None:
                # Invalid OPCODE
                continue
            
            elif handler == POISON:
                break
             
            else:
                
                if not future.set_running_or_notify_cancel():
                    return
                                    
                try:
                    result = handler(*args, **kwds)
                except Exception, e:
                    dbe = DBException(str(e))
                    future.set_exception(dbe)
                else:
                    future.set_result(result)


temp_default_db = None


def clear_default_temp_db_instance():
    global temp_default_db
    
    if temp_default_db is not None:
        temp_default_db.close()
        temp_default_db = None
        os.unlink('%s/main.db' % get_temp_dir())


def get_default_temp_db_instance():
    global temp_default_db
    
    if temp_default_db is None:
        create_temp_dir()
        temp_default_db = SQLiteDBMS('%s/main.db' % get_temp_dir())
        
    return temp_default_db


def get_default_persistent_db_instance():
    """
    At some point I'll want to have persistent DB for storing the KB and other
    information across different w3af processes, or simply to save the findings
    in a KB and don't remove them. I'm adding this method as a reminder of
    where it should be done.
    """
    return get_default_temp_db_instance()
