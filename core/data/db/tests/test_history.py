# -*- coding: UTF-8 -*-
'''
Copyright 2012 Andres Riancho

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
import random
import unittest
import time
import os.path

from nose.plugins.attrib import attr

import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb

from core.controllers.misc.temp_dir import create_temp_dir, remove_temp_dir
from core.data.db.history import HistoryItem
from core.data.fuzzer.fuzzer import rand_alnum
from core.data.request.fuzzable_request import FuzzableRequest as FuzzReq
from core.data.parsers.url import URL
from core.data.url.HTTPResponse import HTTPResponse
from core.data.dc.headers import Headers


@attr('smoke')
class TestHistoryItem(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        cf.cf.cleanup()
        cf.cf.save('session_name',
                'defaultSession' + '-' + time.strftime('%Y-%b-%d_%H-%M-%S'))
        create_temp_dir()

    def tearDown(self):
        remove_temp_dir()
        kb.kb.cleanup()
        cf.cf.cleanup()

    def test_single_db(self):
        h1 = HistoryItem()
        h2 = HistoryItem()
        self.assertEqual(h1._db, h2._db)
    
    def test_special_chars_in_db_filename(self):
        kb.kb.cleanup()
        cf.cf.cleanup()
        cf.cf.save('session_name', 'db_foo-:3128!.db')
        create_temp_dir()
        h1 = HistoryItem()
    
    def test_find(self):
        find_id = random.randint(1, 499)
        url = URL('http://w3af.org/a/b/foobar.php?foo=123')
        tag_value = rand_alnum(10)
        for i in xrange(0, 500):
            fr = FuzzReq(url, dc={'a': ['1']})
            code = 200
            if i == find_id:
                code = 302
            
            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(code, '<html>',hdr, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.set_id(i)
            h1.response = res
            if i == find_id:
                h1.toggleMark()
                h1.updateTag(tag_value)
            h1.save()
        h2 = HistoryItem()
        self.assertEqual(len(h2.find([('tag', "%"+tag_value+"%", 'like')])), 1)
        self.assertEqual(len(h2.find([('code', 302, '=')])), 1)
        self.assertEqual(len(h2.find([('mark', 1, '=')])), 1)
        self.assertEqual(len(h2.find([('has_qs', 1, '=')])), 500)
        self.assertEqual(len(h2.find([('has_qs', 1, '=')], resultLimit=10)), 10)
        results = h2.find([('has_qs', 1, '=')], resultLimit=1, orderData=[('id','desc')])
        self.assertEqual(results[0].id, 499)
        search_data = []
        search_data.append(('id', find_id + 1, "<"))
        search_data.append(('id', find_id - 1, ">"))
        self.assertEqual(len(h2.find(search_data)), 1)

    def test_mark(self):
        mark_id = random.randint(1, 499)
        url = URL('http://w3af.org/a/b/c.php')
        for i in xrange(0, 500):
            fr = FuzzReq(url, dc={'a': ['1']})
            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(200, '<html>', hdr, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.set_id(i)
            h1.response = res
            if i == mark_id:
                h1.toggleMark()
            h1.save()
        h2 = HistoryItem()
        h2.load(mark_id)
        self.assertTrue(h2.mark)

    def test_save_load(self):
        i = random.randint(1, 499)
        url = URL('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>',hdr, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.set_id(i)
        h1.response = res
        h1.save()
        h2 = HistoryItem()
        h2.load(i)
        self.assertEqual(h1.request, h2.request)
        self.assertEqual(h1.response.body, h2.response.body)

    def test_delete(self):
        i = random.randint(1, 499)
        url = URL('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>',hdr, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.set_id(i)
        h1.response = res
        h1.save()
        h1.delete(i)
        try:
            h2 = h1.read(i)
        except:
            h2 = None
        self.assertEqual(h2, None)

    def test_clear(self):
        i = random.randint(1, 499)
        url = URL('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>',hdr, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.set_id(i)
        h1.response = res
        h1.save()
        h1.clear()
        try:
            h2 = h1.read(i)
        except:
            h2 = None
        self.assertEqual(h2, None)
        self.assertFalse(os.path.exists(h1._session_dir))

    def test_tag(self):
        tag_id = random.randint(501, 999)
        tag_value = rand_alnum(10)
        url = URL('http://w3af.org/a/b/c.php')

        for i in xrange(501, 1000):
            fr = FuzzReq(url, dc={'a': ['1']})
            hdr = Headers([('Content-Type', 'text/html')])
            res = HTTPResponse(200, '<html>',hdr, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.set_id(i)
            h1.response = res
            if i == tag_id:
                h1.updateTag(tag_value)
            h1.save()

        h2 = HistoryItem()
        h2.load(tag_id)
        self.assertEqual(h2.tag, tag_value)

        