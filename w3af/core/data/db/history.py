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
import time
import threading
import zipfile
import msgpack

from functools import wraps
from shutil import rmtree

import w3af.core.controllers.output_manager as om

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
    """
    Represents history item
    """

    _db = None
    _DATA_TABLE = 'history_items'
    _COLUMNS = [
        ('id', 'INTEGER'),
        ('url', 'TEXT'),
        ('code', 'INTEGER'),
        ('tag', 'TEXT'),
        ('mark', 'INTEGER'),
        ('info', 'TEXT'),
        ('time', 'FLOAT'),
        ('msg', 'TEXT'),
        ('content_type', 'TEXT'),
        ('charset', 'TEXT'),
        ('method', 'TEXT'),
        ('response_size', 'INTEGER'),
        ('codef', 'INTEGER'),
        ('alias', 'TEXT'),
        ('has_qs', 'INTEGER')
    ]
    _PRIMARY_KEY_COLUMNS = ('id',)
    _INDEX_COLUMNS = ('alias',)

    _EXTENSION = 'trace'
    _MSGPACK_CANARY = 'cute-and-yellow'

    _TMP_EXTENSION = 'tmp'

    _COMPRESSED_EXTENSION = 'zip'
    _COMPRESSED_FILE_BATCH = 150
    _UNCOMPRESSED_FILES = 50
    _COMPRESSION_LEVEL = 7

    _MIN_FILE_COUNT = _COMPRESSED_FILE_BATCH + _UNCOMPRESSED_FILES

    _pending_compression_jobs = []
    _latest_compression_job_end = 0

    id = None
    url = None
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
    charset = None

    history_lock = threading.RLock()
    compression_lock = threading.RLock()

    def __init__(self):
        self._db = get_default_temp_db_instance()
        
        self._session_dir = os.path.join(get_temp_dir(),
                                         self._db.get_file_name() + '_traces')

    def get_session_dir(self):
        return self._session_dir

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
            self._request, resp = self.load_from_file(self.id)
            self._response = resp
        return resp

    def set_response(self, resp):
        self._response = resp

    response = property(get_response, set_response)

    def get_request(self):
        req = self._request
        if not req and self.id:
            req, self._response = self.load_from_file(self.id)
            self._request = req
        return req

    def set_request(self, req):
        self._request = req

    request = property(get_request, set_request)
    
    @verify_has_db
    def find(self, search_data, result_limit=-1, order_data=None):
        """
        Make complex search.
            search_data = {name: (value, operator), ...}
            order_data = [(name, direction)]
        """
        order_data = order_data or []
        result = []

        sql = 'SELECT * FROM ' + self._DATA_TABLE
        where = WhereHelper(search_data)
        sql += where.sql()

        order_by = ''
        #
        # TODO we need to move SQL code to parent class
        #
        for item in order_data:
            order_by += item[0] + ' ' + item[1] + ','
        order_by = order_by[:-1]

        if order_by:
            sql += ' ORDER BY ' + order_by

        sql += ' LIMIT ' + str(result_limit)
        try:
            for row in self._db.select(sql, where.values()):
                item = self.__class__()
                item._load_from_row(row)
                result.append(item)
        except DBException:
            msg = 'You performed an invalid search. Please verify your syntax.'
            raise DBException(msg)
        return result

    def _load_from_row(self, row):
        """
        Load data from row with all columns
        """
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

    def _get_trace_filename_for_id(self, _id):
        return os.path.join(self._session_dir, '%s.%s' % (_id, self._EXTENSION))

    def _load_from_trace_file(self, _id):
        """
        Load a request/response from a trace file on disk. This is the
        simplest implementation, without any retries for concurrency issues.

        :param _id: The request-response ID
        :return: A tuple containing request and response instances
        """
        file_name = self._get_trace_filename_for_id(_id)

        if not os.path.exists(file_name):
            raise TraceReadException('Trace file %s does not exist' % file_name)

        # The file exists, but the contents might not be all on-disk yet
        serialized_req_res = open(file_name, 'rb').read()
        return self._load_from_string(serialized_req_res)

    def _load_from_string(self, serialized_req_res):
        try:
            data = msgpack.loads(serialized_req_res, use_list=True)
        except ValueError:
            # ValueError: Extra data. returned when msgpack finds invalid
            # data in the file
            raise TraceReadException('Failed to load %s' % serialized_req_res)

        try:
            request_dict, response_dict, canary = data
        except TypeError:
            # https://github.com/andresriancho/w3af/issues/1101
            # 'NoneType' object is not iterable
            raise TraceReadException('Not all components found in %s' % serialized_req_res)

        if not canary == self._MSGPACK_CANARY:
            # read failed, most likely because the file write is not
            # complete but for some reason it was a valid msgpack file
            raise TraceReadException('Invalid canary in %s' % serialized_req_res)

        request = HTTPRequest.from_dict(request_dict)
        response = HTTPResponse.from_dict(response_dict)
        return request, response

    def _load_from_trace_file_concurrent(self, _id):
        """
        Load a request/response from a trace file on disk, using retries
        and error handling to make sure all concurrency issues are handled.

        :param _id: The request-response ID
        :return: A tuple containing request and response instances
        """
        wait_time = 0.05

        #
        # Retry the read a few times to handle concurrency issues
        #
        for _ in xrange(int(1 / wait_time)):
            try:
                return self._load_from_trace_file(_id)
            except TraceReadException as e:
                args = (_id, e)
                msg = 'Failed to read trace file %s: "%s"'
                om.out.debug(msg % args)

                time.sleep(wait_time)

        else:
            msg = 'Timeout expecting trace file "%s" to be ready'
            file_name = self._get_trace_filename_for_id(_id)
            raise DBException(msg % file_name)

    def load_from_file(self, _id):
        """
        Loads a request/response from a trace file on disk. Two different
        options exist:

            * The file is compressed inside a zip
            * The file is uncompressed in a trace

        :param _id: The request-response ID
        :return: A tuple containing request and response instances
        """
        #
        # First we check if the trace file exists and try to load it from
        # the uncompressed trace
        #
        file_name = self._get_trace_filename_for_id(_id)

        if os.path.exists(file_name):
            return self._load_from_trace_file_concurrent(_id)

        #
        # The trace file doesn't exist, try to find the zip file where the
        # compressed file lives and read it from there
        #
        try:
            return self._load_from_zip(_id)
        except TraceReadException as e:
            msg = 'Failed to load trace %s from zip file: "%s"'
            args = (_id, e)
            om.out.debug(msg % args)

            #
            # Give the .trace file a last chance, it might be possible that when
            # we checked for os.path.exists(file_name) at the beginning of this
            # method the file wasn't there yet, but is on disk now
            #
            if os.path.exists(file_name):
                return self._load_from_trace_file_concurrent(_id)

            raise TraceReadException('No zip nor trace file for ID %s' % _id)

    def _load_from_zip(self, _id):
        files = os.listdir(self.get_session_dir())
        files = [f for f in files if f.endswith(self._COMPRESSED_EXTENSION)]

        for zip_file in files:
            start, end = get_zip_id_range(zip_file)

            if start <= _id <= end:
                return self._load_from_zip_file(_id, zip_file)

        raise TraceReadException('No zip file contains %s' % _id)

    def _load_from_zip_file(self, _id, zip_file):
        try:
            _zip = zipfile.ZipFile(os.path.join(self.get_session_dir(), zip_file))
        except zipfile.BadZipfile:
            # We get here when the zip file has an invalid format
            #
            # This is most likely because one thread is writing to disk and
            # another is trying to read from it
            msg = 'Zip file %s has an invalid format'
            args = (zip_file,)
            raise TraceReadException(msg % args)

        try:
            serialized_req_res = _zip.read('%s.%s' % (_id, self._EXTENSION))
        except KeyError:
            # We get here when the zip file doesn't contain the trace file
            msg = 'Zip file %s does not contain ID %s'
            args = (zip_file, _id)
            raise TraceReadException(msg % args)

        return self._load_from_string(serialized_req_res)

    @verify_has_db
    def delete(self, _id=None):
        """
        Delete data from DB by ID.
        """
        if _id is None:
            _id = self.id
            
        sql = 'DELETE FROM ' + self._DATA_TABLE + ' WHERE id = ? '
        self._db.execute(sql, (_id,))
        
        fname = self._get_trace_filename_for_id(_id)
        
        try:
            os.remove(fname)
        except OSError:
            pass

    @verify_has_db
    def load(self, _id=None, retry=True):
        """
        Load data from DB by ID
        """
        if _id is None:
            _id = self.id

        sql = 'SELECT * FROM ' + self._DATA_TABLE + ' WHERE id = ? '
        try:
            row = self._db.select_one(sql, (_id,))
        except DBException, dbe:
            msg = ('An unexpected error occurred while searching for id "%s"'
                   ' in table "%s". Original exception: "%s".')
            raise DBException(msg % (_id, self._DATA_TABLE, dbe))

        if row is not None:
            self._load_from_row(row)
            return True

        if not retry:
            #
            # This is the second time load() is called and we end up
            # here, raise an exception and finish our pain.
            #
            msg = ('An internal error occurred while searching for id "%s",'
                   ' even after commit/retry')
            raise DBException(msg % _id)

        #
        # The request/response with _id is not in the DB!
        # Lets do some error handling and try again!
        #
        # According to sqlite3 documentation this db.commit()
        # might fix errors like [0] but it can degrade performance due
        # to disk IO
        #
        # [0] https://sourceforge.net/apps/trac/w3af/ticket/164352 ,
        #
        self._db.commit()
        return self.load(_id=_id, retry=False)

    @verify_has_db
    def read(self, _id):
        """
        Return item by ID
        """
        result_item = self.__class__()
        result_item.load(_id)
        return result_item

    def save(self):
        """
        Save History instance to DB and disk
        """
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
        path_fname = self._get_trace_filename_for_id(self.id)

        try:
            req_res = open(path_fname, 'wb')
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
        msgpack_data = msgpack.dumps(data)

        req_res.write(msgpack_data)
        req_res.close()

        response_id = resp.get_id()
        self._queue_compression_requests(response_id)

        pending_compression = self._get_pending_compression_job()

        if pending_compression is not None:
            self._process_pending_compression(pending_compression)

        return True

    def _get_pending_compression_job(self):
        with HistoryItem.compression_lock:
            try:
                return self._pending_compression_jobs.pop(0)
            except IndexError:
                return None

    def _queue_compression_requests(self, response_id):
        """
        Every N calls to save() check if there are enough files to compress in
        the session directory and create a PendingCompressionJob instance.

        Save that instance in _pending_compression_jobs. The _get_pending_compression_job
        method will be used to read jobs from that list in a thread-safe way.

        :param response_id:
        :return:
        """
        # Performance boost that prevents the disk access and lock from below
        # from running on each save()
        if response_id % 100 != 0:
            return

        with HistoryItem.compression_lock:
            #
            # Get the list of files to compress, checking that we have enough to
            # proceed with compression
            #
            session_dir = self._session_dir

            files = [f for f in os.listdir(session_dir) if f.endswith(self._EXTENSION)]
            files = [os.path.join(session_dir, f) for f in files]

            if len(files) <= HistoryItem._MIN_FILE_COUNT:
                return

            #
            # Sort by ID and remove the last 50 from the list to avoid
            # compression-decompression CPU waste and concurrency issues with trace
            # files that have not yet completed writing to disk
            #
            files.sort(key=lambda trace_file: get_trace_id(trace_file))
            files = files[:-self._UNCOMPRESSED_FILES]

            #
            # Compress in 150 file batches, and making sure that the filenames
            # are numerically ordered. We need this order to have 1, 2, ... 150 in
            # the same file. The filename will be named `1-150.zip` which will later
            # be used to find the uncompressed trace.
            #
            while True:
                current_batch_files = files[:self._COMPRESSED_FILE_BATCH]

                if len(current_batch_files) != self._COMPRESSED_FILE_BATCH:
                    # There are not enough files in this batch
                    break

                # Compress the oldest 150 files into a zip
                start = get_trace_id(current_batch_files[0])
                end = get_trace_id(current_batch_files[-1])

                if start <= HistoryItem._latest_compression_job_end:
                    # This check prevents overlapping PendingCompressionJob from
                    # being added to the list by different threads
                    break

                pending_compression = PendingCompressionJob(start, end)
                HistoryItem._latest_compression_job_end = end
                HistoryItem._pending_compression_jobs.append(pending_compression)

                # Ignore the first 150, these were already processed, and continue
                # iterating in the while loop
                files = files[self._COMPRESSED_FILE_BATCH:]

    def _process_pending_compression(self, pending_compression):
        """
        Compress a PendingCompressionJob, usually the 150 oldest files in the
        session directory together inside a zip file.

        Not compressing all files because the newest ones might be read by
        plugins and we don't want to decompress them right after compressing
        them (waste of CPU).

        :return: None
        """
        session_dir = self._session_dir
        trace_range = xrange(pending_compression.start, pending_compression.end + 1)

        files = ['%s.%s' % (i, HistoryItem._EXTENSION) for i in trace_range]
        files = [os.path.join(session_dir, filename) for filename in files]

        #
        # Target zip filename
        #
        compressed_filename = '%s-%s.%s' % (pending_compression.start,
                                            pending_compression.end,
                                            self._COMPRESSED_EXTENSION)
        compressed_filename = os.path.join(session_dir, compressed_filename)

        # To prevent race conditions between a thread that is writing the zip
        # file and another thread that is attempting to read from it, we first
        # write the contents of the zip file to a .tmp file, and when all the
        # contents have been written and flushed, rename the file to a zip file
        compressed_filename_temp = '%s.%s' % (compressed_filename, self._TMP_EXTENSION)

        #
        # I run some tests with tarfile to check if tar + gzip or tar + bzip2
        # were faster / better suited for this task. This is what I got when
        # running test_save_load_compressed():
        #
        #   zip
        #       150 request - responses compressed in: 125 k
        #       Unittest run time: 0.3 seconds
        #
        #   tar.gz
        #       150 request - responses compressed in: 15 k
        #       Unittest run time: 1.6 seconds
        #
        #
        #   tar.bz2
        #       150 request - responses compressed in: 9 k
        #       Unittest run time: 7.0 seconds
        #
        # Note that the unittest forces compression of 150 requests and then
        # reads each of those compressed requests one by one from the
        # compressed archive.
        #
        # Summary: If you want to change the compression algorithm make sure
        #          that it is better than `zip`.
        #
        _zip = zipfile.ZipFile(file=compressed_filename_temp,
                               mode='w',
                               compression=zipfile.ZIP_DEFLATED)

        for filename in files:
            try:
                _zip.write(filename=filename,
                           arcname='%s.%s' % (get_trace_id(filename), self._EXTENSION))
            except OSError:
                # The file might not exist
                continue

        _zip.close()

        # Rename the file to .zip only after all the contents have been flushed
        # to disk by .close().
        #
        # This prevents race conditions
        os.rename(compressed_filename_temp, compressed_filename)

        #
        # And now remove the already compressed files
        #
        for filename in files:
            try:
                os.remove(filename)
            except OSError:
                # The file might not exist
                continue

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

    def __repr__(self):
        return '<HistoryItem %s %s>' % (self.method, self.url)


def get_trace_id(trace_file):
    return int(trace_file.rsplit('/')[-1].rsplit('.')[-2])


def get_zip_id_range(zip_file):
    name_ext = zip_file.rsplit('/')[-1]
    name = name_ext.split('.')[0]
    start, end = name.split('-')
    return int(start), int(end)


class TraceReadException(Exception):
    pass


class PendingCompressionJob(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
