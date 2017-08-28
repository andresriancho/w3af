"""
history.py

Copyright 2009 Andres Riancho

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

import os
import gzip
import time
import threading
import msgpack

from functools import wraps
from shutil import rmtree

from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.controllers.exceptions import DBException
from w3af.core.data.db.where_helper import WhereHelper
from w3af.core.data.db.dbms import get_default_temp_db_instance
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest


def verify_has_db(meth):
    
    @wraps(meth)
    def inner_verify_has_db(self, *args, **kwds):
        if self._db is None:
            raise RuntimeError('The database is not initialized yet.')
        return meth(self, *args, **kwds)
    
    return inner_verify_has_db


class HistoryItem(object):
    """Represents history item."""

    _db = None
    _DATA_TABLE = 'history_items'
    _COLUMNS = [
        ('id', 'INTEGER'), ('url', 'TEXT'), ('code', 'INTEGER'),
        ('tag', 'TEXT'), ('mark', 'INTEGER'), ('info', 'TEXT'),
        ('time', 'FLOAT'), ('msg', 'TEXT'), ('content_type', 'TEXT'),
        ('charset', 'TEXT'), ('method', 'TEXT'), ('response_size', 'INTEGER'),
        ('codef', 'INTEGER'), ('alias', 'TEXT'), ('has_qs', 'INTEGER')
    ]
    _PRIMARY_KEY_COLUMNS = ('id',)
    _INDEX_COLUMNS = ('alias',)

    _EXTENSION = '.trace'
    _MSGPACK_CANARY = 'cute-and-yellow'

    COMPRESSION_LEVEL = 2

    id = None
    _request = None
    _response = None
    info = None
    mark = False
    tag = ''
    content_type = ''
    response_size = 0
    method = 'GET'
    msg = 'OK'
    code = 200
    time = 0.2

    history_lock = threading.RLock()

    def __init__(self):
        self._db = get_default_temp_db_instance()
        
        self._session_dir = os.path.join(get_temp_dir(),
                                         self._db.get_file_name() + '_traces')

    def init(self):
        self.init_traces_dir()
        self.init_db()

    def init_traces_dir(self):
        with self.history_lock:
            if not os.path.exists(self._session_dir):
                os.mkdir(self._session_dir)
    
    def init_db(self):
        """
        Init history table and indexes.
        """
        with self.history_lock:
            tablename = self.get_table_name()
            if not self._db.table_exists(tablename):
                
                pk_cols = self.get_primary_key_columns()
                idx_cols = self.get_index_columns()
                
                self._db.create_table(tablename, self.get_columns(),
                                      pk_cols).result()
                self._db.create_index(tablename, idx_cols).result()
            
    def get_response(self):
        resp = self._response
        if not resp and self.id:
            self._request, resp = self._load_from_file(self.id)
            self._response = resp
        return resp

    def set_response(self, resp):
        self._response = resp

    response = property(get_response, set_response)

    def get_request(self):
        req = self._request
        if not req and self.id:
            req, self._response = self._load_from_file(self.id)
            self._request = req
        return req

    def set_request(self, req):
        self._request = req

    request = property(get_request, set_request)
    
    @verify_has_db
    def find(self, searchData, result_limit=-1, orderData=[], full=False):
        """Make complex search.
        search_data = {name: (value, operator), ...}
        orderData = [(name, direction)]
        """
        result = []
        sql = 'SELECT * FROM ' + self._DATA_TABLE
        where = WhereHelper(searchData)
        sql += where.sql()
        orderby = ""
        #
        # TODO we need to move SQL code to parent class
        #
        for item in orderData:
            orderby += item[0] + " " + item[1] + ","
        orderby = orderby[:-1]

        if orderby:
            sql += " ORDER BY " + orderby

        sql += ' LIMIT ' + str(result_limit)
        try:
            for row in self._db.select(sql, where.values()):
                item = self.__class__()
                item._load_from_row(row, full)
                result.append(item)
        except DBException:
            msg = 'You performed an invalid search. Please verify your syntax.'
            raise DBException(msg)
        return result

    def _load_from_row(self, row, full=True):
        """Load data from row with all columns."""
        self.id = row[0]
        self.url = row[1]
        self.code = row[2]
        self.tag = row[3]
        self.mark = bool(row[4])
        self.info = row[5]
        self.time = float(row[6])
        self.msg = row[7]
        self.content_type = row[8]
        self.charset = row[9]
        self.method = row[10]
        self.response_size = int(row[11])

    def _get_fname_for_id(self, _id):
        return os.path.join(self._session_dir, str(_id) + self._EXTENSION)
    
    def _load_from_file(self, id):
        fname = self._get_fname_for_id(id)
        WAIT_TIME = 0.05

        #
        #    Due to some concurrency issues, we need to perform these checks
        #
        for _ in xrange(int(1 / WAIT_TIME)):
            if not os.path.exists(fname):
                time.sleep(WAIT_TIME)
                continue

            # Ok... the file exists, but it might still be being written
            req_res = gzip.open(fname, 'rb', compresslevel=self.COMPRESSION_LEVEL)

            try:
                data = msgpack.load(req_res, use_list=True)
            except ValueError:
                # ValueError: Extra data. returned when msgpack finds invalid
                # data in the file
                req_res.close()
                time.sleep(WAIT_TIME)
                continue

            try:
                request_dict, response_dict, canary = data
            except TypeError:
                # https://github.com/andresriancho/w3af/issues/1101
                # 'NoneType' object is not iterable
                req_res.close()
                time.sleep(WAIT_TIME)
                continue

            if not canary == self._MSGPACK_CANARY:
                # read failed, most likely because the file write is not
                # complete but for some reason it was a valid msgpack file
                req_res.close()
                time.sleep(WAIT_TIME)
                continue

            # Success!
            req_res.close()

            request = HTTPRequest.from_dict(request_dict)
            response = HTTPResponse.from_dict(response_dict)
            return request, response

        else:
            msg = 'Timeout expecting trace file to be ready "%s"' % fname
            raise IOError(msg)

    @verify_has_db
    def delete(self, _id=None):
        """Delete data from DB by ID."""
        if _id is None:
            _id = self.id
            
        sql = 'DELETE FROM ' + self._DATA_TABLE + ' WHERE id = ? '
        self._db.execute(sql, (_id,))
        
        fname = self._get_fname_for_id(_id)
        
        try:
            os.remove(fname)
        except OSError:
            pass

    @verify_has_db
    def load(self, _id=None, full=True, retry=True):
        """Load data from DB by ID."""
        if not _id:
            _id = self.id

        sql = 'SELECT * FROM ' + self._DATA_TABLE + ' WHERE id = ? '
        try:
            row = self._db.select_one(sql, (_id,))
        except DBException, dbe:
            msg = 'An unexpected error occurred while searching for id "%s"'\
                  ' in table "%s". Original exception: "%s".'
            raise DBException(msg % (_id, self._DATA_TABLE, dbe))
        else:
            if row is not None:
                self._load_from_row(row, full)
            else:
                # The request/response with 'id' == id is not in the DB!
                # Lets do some "error handling" and try again!

                if retry:
                    #    TODO:
                    #    According to sqlite3 documentation this db.commit()
                    #    might fix errors like
                    #    https://sourceforge.net/apps/trac/w3af/ticket/164352 ,
                    #    but it can degrade performance due to disk IO
                    #
                    self._db.commit()
                    self.load(_id=_id, full=full, retry=False)
                else:
                    # This is the second time load() is called and we end up
                    # here, raise an exception and finish our pain.
                    msg = ('An internal error occurred while searching for '
                           'id "%s", even after commit/retry' % _id)
                    raise DBException(msg)

        return True

    @verify_has_db
    def read(self, _id, full=True):
        """Return item by ID."""
        result_item = self.__class__()
        result_item.load(_id, full)
        return result_item

    def save(self):
        """Save object into DB."""
        resp = self.response
        code = int(resp.get_code()) / 100

        values = [resp.get_id(),
                  self.request.get_uri().url_string,
                  resp.get_code(),
                  self.tag,
                  int(self.mark),
                  str(resp.info()),
                  resp.get_wait_time(),
                  resp.get_msg(),
                  resp.content_type,
                  resp.charset,
                  self.request.get_method(),
                  len(resp.body),
                  code,
                  resp.get_alias(),
                  int(self.request.get_uri().has_query_string())]

        if not self.id:
            sql = ('INSERT INTO %s '
                   '(id, url, code, tag, mark, info, time, msg, content_type, '
                   'charset, method, response_size, codef, alias, has_qs) '
                   'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)' % self._DATA_TABLE)
            self._db.execute(sql, values)
            self.id = self.response.get_id()
        else:
            values.append(self.id)
            sql = ('UPDATE %s'
                   ' SET id = ?, url = ?, code = ?, tag = ?, mark = ?,'
                   ' info = ?, time = ?, msg = ?, content_type = ?,'
                   ' charset = ?, method = ?, response_size = ?, codef = ?,'
                   ' alias = ?, has_qs = ? WHERE id = ?' % self._DATA_TABLE)
            self._db.execute(sql, values)

        #
        # Save raw data to file
        #
        path_fname = self._get_fname_for_id(self.id)

        try:
            req_res = gzip.open(path_fname, 'wb',
                                compresslevel=self.COMPRESSION_LEVEL)
        except IOError:
            # We get here when the path_fname does not exist (for some reason)
            # and want to analyze exactly why to be able to fix the issue in
            # the future.
            #
            # Now the path_fname looks like:
            #   /root/.w3af/tmp/19524/main.db_traces/1.trace
            #
            # I want to investigate which path doesn't exist, so I'm starting
            # from the first and add directories until reaching the last one
            #
            # https://github.com/andresriancho/w3af/issues/9022
            path, fname = os.path.split(path_fname)
            split_path = path.split('/')

            for i in xrange(len(split_path) + 1):
                test_path = '/'.join(split_path[:i])
                if not os.path.exists(test_path):
                    msg = ('Directory does not exist: "%s" while trying to'
                           ' write DB history to "%s"')
                    raise IOError(msg % (test_path, path_fname))

            raise

        data = (self.request.to_dict(),
                self.response.to_dict(),
                self._MSGPACK_CANARY)
        msgpack.dump(data, req_res)
        req_res.close()
        
        return True

    def get_columns(self):
        return self._COLUMNS

    def get_table_name(self):
        return self._DATA_TABLE

    def get_primary_key_columns(self):
        return self._PRIMARY_KEY_COLUMNS

    def get_index_columns(self):
        return self._INDEX_COLUMNS

    def _update_field(self, name, value):
        """Update custom field in DB."""
        sql = 'UPDATE %s SET %s = ? WHERE id = ?' % (self._DATA_TABLE, name)
        self._db.execute(sql, (value, self.id))

    def update_tag(self, value, force_db=False):
        """Update tag."""
        self.tag = value
        if force_db:
            self._update_field('tag', value)

    def toggle_mark(self, force_db=False):
        """Toggle mark state."""
        self.mark = not self.mark
        if force_db:
            self._update_field('mark', int(self.mark))

    def clear(self):
        """Clear history and delete all trace files."""
        if self._db is None:
            return

        # Remove the table if it still exists, I verify if it exists
        # before removing it in order to allow clear() to be called more than
        # once in a consecutive way 
        if self._db.table_exists(self.get_table_name()):
            self._db.clear_table(self.get_table_name()).result()
            
        self._db = None
        
        # It might be the case that another thread removes the session dir
        # at the same time as we, so we simply ignore errors here
        rmtree(self._session_dir, ignore_errors=True)
        
        return True
