'''
db.py

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
import sys

from core.controllers.w3afException import w3afException


class DBClient(object):
    """Simple W3AF DB interface"""

    def __init__(self):
        '''Construct object.'''
        self._filename = None
        self._db = None
        self._insertionCount = 0
        self._commitNumber = 50
        self._dbLock = threading.RLock()
    
    def connect(self):
        '''Open a db connection. To be implemented by children'''
        raise NotImplementedError

    def getFileName(self):
        '''Return DB filename.'''
        return self._filename

    def _commitIfNeeded(self):
        '''Once every N calls to this method, the data is committed to disk.'''
        self._insertionCount += 1
        if self._insertionCount > self._commitNumber:
            try:
                self._db.commit()
            except Exception, e:
                raise w3afException('The database layer of object persistence\
                        raised and exception: ' + str(e) )
            else:
                self._insertionCount = 0

    def retrieve(self, sql, parameters=(), all=False):
        '''Execute SQL and retrieve raws.'''
        
        rows = None
        c = self._db.cursor()
        with self._dbLock:
            try:
                c.execute(sql, parameters)
                rows = c.fetchall() if all else c.fetchone()
            except Exception:
                raise
        return rows

    def execute(self, sql, parameters=()):
        '''Execute SQL statement.'''
        
        c = self._db.cursor()
        with self._dbLock:
            try:
                c.execute(sql, parameters)
                self._commitIfNeeded()
            except Exception, e:
                raise

    def createTable(self, name, columns=(), primaryKeyColumns=[]):
        '''Create table in convenient way.'''
        #
        # Lets create the table
        #
        sql = 'CREATE TABLE ' + name + '('
        for columnData in columns:
            columnName, columnType = columnData
            sql += columnName + ' ' + columnType + ', '
        # Finally the PK
        sql += 'PRIMARY KEY (' + ','.join(primaryKeyColumns) + '))'
        c = self._db.cursor()

        c.execute(sql)
        self._db.commit()

    def createIndex(self, table, columns):
        '''
        Create index for speed and performance

        @parameter table: The table from which you want to create an index from
        @parameter columns: A list of column names.
        '''
        sql = 'CREATE INDEX %s_index ON %s( %s )' % (table, table, ','.join(columns) )
        c = self._db.cursor()

        c.execute(sql)
        self._db.commit()

    def cursor(self):
        '''Simple return cursor object.'''
        return self._db.cursor()

    def close(self):
        '''Commit changes and close the connection to the underlaying db.'''
        self._db.close()
        self._filename = None


class DBClientSQLite(DBClient):
    
    def connect(self, dbname):
        '''Open database file.'''
        # Convert the filename to UTF-8
        # this is needed for windows, and special characters
        #
        # https://sourceforge.net/tracker2/index.php?func=detail&aid=2618162&group_id=170274&atid=853652
        # http://www.sqlite.org/c3ref/open.html
        unicodeFilename = dbname.decode(sys.getfilesystemencoding())
        self._filename = filenameUtf8 = unicodeFilename.encode("utf-8")

        try:
            ### FIXME: check_same_thread=False
            self._db = sqlite3.connect(filenameUtf8, check_same_thread=False)
            self._db.text_factory = str
        except Exception, e:
            raise w3afException('Failed to create the database in file "%s". '
                    'Exception: %s' % (filenameUtf8, e))


class DBCLientPGSql(DBClient):

    def connect(self):
        import psycopg2
        self._db = psycopg2.connect(("dbname='test' user='postgres' "
                                 "host='localhost' password='postgres'"))

# Use this client
DB = DBClientSQLite


class WhereHelper(object):
    '''Simple WHERE condition maker.'''
    conditions = {}
    _values = []

    def __init__(self, conditions = {}):
        '''Construct object.'''
        self.conditions = conditions

    def values(self):
        '''Return values for prep.statements.'''
        if not self._values:
            self.sql()
        return self._values

    def _makePair(self, field, value, oper='=',  conjunction='AND'):
        '''Auxiliary method.'''
        result = ' ' + conjunction + ' ' + field + ' ' + oper + ' ?'
        return (result, value)

    def sql(self, whereStr=True):
        '''Return SQL string.'''
        result = ''
        self._values = []

        for cond in self.conditions:
            if isinstance(cond[0], list):
                item, oper = cond
                tmpWhere = ''
                for tmpField in item:
                    tmpName, tmpValue, tmpOper = tmpField
                    sql, value = self._makePair(tmpName, tmpValue, tmpOper, oper)
                    self._values.append(value)
                    tmpWhere += sql
                if tmpWhere:
                    result += " AND (" + tmpWhere[len(oper)+1:] + ")"
            else:
                sql, value = self._makePair(cond[0], cond[1], cond[2])
                self._values.append(value)
                result += sql
        result = result[5:]

        if whereStr and result:
            result = ' WHERE ' + result

        return result

    def __str__(self):
        return self.sql() + ' | ' + str(self.values())


class DbMgr(object):
    '''Singleton database connection pool manager.'''
    
    def __init__(self):
        _class = self.__class__
        if _class._do_init_:
            # Pool size
            self._poolsize = 10
            self.set_pool_size()
            # Lock
            self._lock = threading.Lock()
            # Free Database Clients list
            self._free_db_list = []
            # Checked Out Db
            self._checked_out = 0
            _class._do_init_ = False
    
    def __new__(cls):
        '''
        This gives the class its "singleton-ness".
        '''
        _dbmgrstr = '_dbmgr_instance'
        if not cls.__dict__.get(_dbmgrstr):
            setattr(cls, _dbmgrstr, object.__new__(cls))
            cls._do_init_ = True
        return getattr(cls, _dbmgrstr)
    
    def execute(self, sql, params=[]):
        return self.process_request('execute', sql, parameters=params)
    
    def retrieve(self, sql, params=[], all=False):
        return self.process_request('retrieve', sql, parameters=params, all=all)
    
    def __getattr__(self, attrname):
        # FIXME: See why this is not properly releasing the connections
        theclient = self._get_avail_dbclient()
        attr = getattr(theclient, attrname)
        self._free_dbclient(theclient)
        return attr
    
    def set_pool_size(self, size=10):
        '''Set the size of the database connection pool.'''
        # TODO: deal with shrinking the pool.
        if self._poolsize > size:
            pass
        self._poolsize = size
    
    def process_request(self, method, *args, **kwargs):
        '''Submit a request to an available database client.'''
        theclient = self._get_avail_dbclient()
        if theclient:
            try:
                return getattr(theclient, method)(*args, **kwargs)
            finally:
                self._free_dbclient(theclient)
        else:
            raise Exception('All %d database connections are busy.'
                            % self._poolsize)
    
    def _get_avail_dbclient(self):
        '''Return an available DbClient, if any; otherwise returns None.'''
        with self._lock:

            retry_count = 0
            theclient = None
            
            while retry_count < 20:
                if self._free_db_list:
                    # Pick the first Client from the List
                    # to get round-robin usage
                    theclient = self._free_db_list.pop(0)
                elif self._checked_out < self._poolsize:
                    theclient = self._create_dbclient()
            
                if theclient:
                    self._checked_out += 1
                    break
                else:
                    retry_count += 1
                    import time
                    time.sleep(0.2)
                
            return theclient
    
    def _free_dbclient(self, theclient):
        # Put theclient at the end of the list
        self._free_db_list.append(theclient)
        self._checked_out -= 1
    
    def _create_dbclient(self):
        '''Return the appropriate database client'''
        # Make the database connection.
        return DB()
    
    def shutdown(self):
        '''Shutdown the database connections.'''
        # TODO: write
        pass
