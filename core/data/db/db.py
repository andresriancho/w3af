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

class DB(object):
    """Simple W3AF DB interface"""

    def __init__(self):
        '''Construct object.'''
        self._filename = None
        self._db = None
        self._insertionCount = 0
        self._commitNumber = 50
        self._dbLock = threading.RLock()

    def open(self, filename):
        '''Open database file.'''
        # Convert the filename to UTF-8
        # this is needed for windows, and special characters
        #
        # https://sourceforge.net/tracker2/index.php?func=detail&aid=2618162&group_id=170274&atid=853652
        # http://www.sqlite.org/c3ref/open.html
        unicodeFilename = filename.decode(sys.getfilesystemencoding())
        filenameUtf8 = unicodeFilename.encode("utf-8")

        try:
            ### FIXME: check_same_thread=False
            self._db = sqlite3.connect(filenameUtf8, check_same_thread=False)
            self._db.text_factory = str
            # Now we save the data to the attributes
            self._filename = filenameUtf8
        except Exception, e:
            raise w3afException('Failed to create the database in file "'\
                    + filenameUtf8 +'". Exception: ' + str(e) )

    def getFileName(self):
        '''Return DB filename.'''
        return self._filename

    def _commitIfNeeded( self ):
        '''Once every N calls to this method, the data is commited to disk.'''
        self._insertionCount += 1
        if self._insertionCount > self._commitNumber:
            try:
                self._db.commit()
            except Exception, e:
                raise w3afException('The database layer of object persistence\
                        raised and exception: ' + str(e) )
            else:
                self._insertionCount = 0

    def retrieveAll(self, sql, parameters=[]):
        '''Execute SQL and retrieve all raw.'''
        c = self._db.cursor()
        rows = []
        with self._dbLock:
            try:
                c.execute(sql, parameters)
                rows = c.fetchall()
            except Exception, e:
                raise e
            return rows

    def retrieve(self, sql, parameters=[]):
        '''Execute SQL and retrieve one raw.'''
        c = self._db.cursor()
        row = None
        with self._dbLock:
            try:
                c.execute(sql, parameters)
                row = c.fetchone()
            except Exception, e:
                raise e
            return row

    def execute(self, sql, parameters=[]):
        '''Execute SQL statement.'''
        c = self._db.cursor()
        with self._dbLock:
            try:
                c.execute(sql, parameters)
                self._commitIfNeeded()
            except Exception, e:
                raise e

    def createTable(self, name, columns=[], primaryKeyColumns=[]):
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

    def createIndex(self, table, columns ):
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


