# -*- coding: UTF-8 -*-
"""
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
import zipfile
import random
import unittest
import os.path

from nose.plugins.attrib import attr

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.exceptions import DBException
from w3af.core.controllers.misc.temp_dir import create_temp_dir, remove_temp_dir
from w3af.core.data.db.dbms import get_default_temp_db_instance
from w3af.core.data.db.history import HistoryItem, TraceReadException
from w3af.core.data.dc.headers import Headers
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.plugins.tests.helper import LOREM


@attr('smoke')
class TestHistoryItem(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        create_temp_dir()
        HistoryItem().init()

    def tearDown(self):
        remove_temp_dir()
        HistoryItem().clear()
        kb.kb.cleanup()

    def test_single_db(self):
        h1 = HistoryItem()
        h2 = HistoryItem()
        self.assertEqual(h1._db, h2._db)

    def test_find(self):
        find_id = random.randint(1, 499)
        url = URL('http://w3af.org/a/b/foobar.php?foo=123')
        tag_value = rand_alnum(10)

        for i in xrange(0, 500):
            request = HTTPRequest(url, data='a=1')
            code = 200
            if i == find_id:
                code = 302

            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(code, '<html>', hdr, url, url)
            h1 = HistoryItem()
            h1.request = request
            res.set_id(i)
            h1.response = res

            if i == find_id:
                h1.toggle_mark()
                h1.update_tag(tag_value)
            h1.save()

        h2 = HistoryItem()
        self.assertEqual(len(h2.find([('tag', "%" + tag_value + "%", 'like')])), 1)
        self.assertEqual(len(h2.find([('code', 302, '=')])), 1)
        self.assertEqual(len(h2.find([('mark', 1, '=')])), 1)
        self.assertEqual(len(h2.find([('has_qs', 1, '=')])), 500)
        self.assertEqual(len(h2.find([('has_qs', 1, '=')], result_limit=10)), 10)
        results = h2.find([('has_qs', 1, '=')], result_limit=1, order_data=[('id', 'desc')])
        self.assertEqual(results[0].id, 499)
        search_data = [('id', find_id + 1, "<"),
                       ('id', find_id - 1, ">")]
        self.assertEqual(len(h2.find(search_data)), 1)

    def test_mark(self):
        mark_id = 3
        url = URL('http://w3af.org/a/b/c.php')
        
        for i in xrange(0, 500):
            request = HTTPRequest(url, data='a=1')
            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(200, '<html>', hdr, url, url)
            h1 = HistoryItem()
            h1.request = request
            res.set_id(i)
            h1.response = res
            if i == mark_id:
                h1.toggle_mark()
            h1.save()

        h2 = HistoryItem()
        h2.load(mark_id)
        self.assertTrue(h2.mark)

        h3 = HistoryItem()
        h3.load(mark_id-1)
        self.assertFalse(h3.mark)

    def test_save_load(self):
        i = random.randint(1, 499)
        url = URL('http://w3af.com/a/b/c.php')
        request = HTTPRequest(url, data='a=1')

        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>', hdr, url, url)

        h1 = HistoryItem()
        h1.request = request
        res.set_id(i)
        h1.response = res
        h1.save()

        h2 = HistoryItem()
        h2.load(i)

        self.assertEqual(h1.request.to_dict(), h2.request.to_dict())
        self.assertEqual(h1.response.body, h2.response.body)

    def test_load_not_exists(self):
        h = HistoryItem()
        self.assertRaises(DBException, h.load, 1)

    def test_save_load_compressed(self):
        force_compression_count = HistoryItem._UNCOMPRESSED_FILES + HistoryItem._COMPRESSED_FILE_BATCH
        force_compression_count += 150

        url = URL('http://w3af.com/a/b/c.php')
        headers = Headers([('Content-Type', 'text/html')])
        body = '<html>' + LOREM * 20

        for i in xrange(1, force_compression_count):
            request = HTTPRequest(url, data='a=%s' % i)

            response = HTTPResponse(200, body, headers, url, url)
            response.set_id(i)

            h = HistoryItem()
            h.request = request
            h.response = response
            h.save()

        compressed_file = os.path.join(h.get_session_dir(), '1-150.zip')
        self.assertTrue(os.path.exists(compressed_file))

        compressed_file_temp = os.path.join(h.get_session_dir(), '1-150.zip.tmp')
        self.assertFalse(os.path.exists(compressed_file_temp))

        expected_files = ['%s.trace' % i for i in range(1, HistoryItem._COMPRESSED_FILE_BATCH + 1)]

        _zip = zipfile.ZipFile(compressed_file, mode='r')
        self.assertEqual(_zip.namelist(), expected_files)

        for i in xrange(1, 100):
            h = HistoryItem()
            h.load(i)

            self.assertEqual(h.request.get_uri(), url)
            self.assertEqual(h.response.get_headers(), headers)
            self.assertEqual(h.response.get_body(), body)

    def test_delete(self):
        i = random.randint(1, 499)
        
        url = URL('http://w3af.com/a/b/c.php')
        request = HTTPRequest(url, data='a=1')
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>', hdr, url, url)
        res.set_id(i)
        
        h1 = HistoryItem()
        h1.request = request
        h1.response = res
        h1.save()
        
        fname = h1._get_trace_filename_for_id(i)
        self.assertTrue(os.path.exists(fname))
        
        h1.delete(i)
        
        self.assertRaises(DBException, h1.read, i)
        self.assertFalse(os.path.exists(fname))

    def test_clear(self):
        url = URL('http://w3af.com/a/b/c.php')
        request = HTTPRequest(url, data='a=1')
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>', hdr, url, url)
        
        h1 = HistoryItem()
        h1.request = request
        res.set_id(1)
        h1.response = res
        h1.save()

        table_name = h1.get_table_name()
        db = get_default_temp_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        clear_result = h1.clear()
        
        self.assertTrue(clear_result)
        self.assertFalse(os.path.exists(h1._session_dir),
                         '%s exists.' % h1._session_dir)
        
        # Changed the meaning of clear a little bit... now it simply removes
        # all rows from the table, not the table itself
        self.assertTrue(db.table_exists(table_name))        

    def test_clear_clear(self):
        url = URL('http://w3af.com/a/b/c.php')
        request = HTTPRequest(url, data='a=1')
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>', hdr, url, url)
        
        h1 = HistoryItem()
        h1.request = request
        res.set_id(1)
        h1.response = res
        h1.save()
        
        h1.clear()
        h1.clear()

    def test_init_init(self):
        # No exceptions should be raised
        HistoryItem().init()
        HistoryItem().init()

    def test_tag(self):
        tag_id = random.randint(501, 999)
        tag_value = rand_alnum(10)
        url = URL('http://w3af.org/a/b/c.php')

        for i in xrange(501, 1000):
            request = HTTPRequest(url, data='a=1')
            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(200, '<html>', hdr, url, url)
            h1 = HistoryItem()
            h1.request = request
            res.set_id(i)
            h1.response = res
            if i == tag_id:
                h1.update_tag(tag_value)
            h1.save()

        h2 = HistoryItem()
        h2.load(tag_id)
        self.assertEqual(h2.tag, tag_value)

    def test_save_load_unicode_decode_error(self):
        url = URL('http://w3af.com/a/b/é.php?x=á')
        request = HTTPRequest(url, data='a=1')
        headers = Headers([('Content-Type', 'text/html')])

        res = HTTPResponse(200, '<html>', headers, url, url)
        res.set_id(1)

        h1 = HistoryItem()
        h1.request = request
        h1.response = res
        h1.save()

        h2 = HistoryItem()
        h2.load(1)

        self.assertEqual(h1.request.to_dict(), h2.request.to_dict())
        self.assertEqual(h1.response.body, h2.response.body)
        self.assertEqual(h1.request.url_object, h2.request.url_object)
