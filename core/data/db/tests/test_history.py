# -*- coding: UTF-8 -*-

import random
import unittest
import string
import time
import os.path
import os

from core.controllers.misc.temp_dir import create_temp_dir, remove_temp_dir
import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb
from core.data.db.history import HistoryItem
from core.data.fuzzer.fuzzer import createRandAlNum

from core.data.request.fuzzableRequest import fuzzableRequest as FuzzReq
from core.data.url.httpResponse import httpResponse, DEFAULT_CHARSET
from core.data.parsers.urlParser import url_object

class TestHistoryItem(unittest.TestCase):

    def setUp(self):
        cf.cf.save('sessionName',
                'defaultSession' + '-' + time.strftime('%Y-%b-%d_%H-%M-%S'))
        create_temp_dir()

    def tearDown(self):
        remove_temp_dir()
        kb.kb.cleanup()

    def test_single_db(self):
        h1 = HistoryItem()
        h2 = HistoryItem()
        self.assertEqual(h1._db, h2._db)

    def test_find(self):
        find_id = random.randint(1, 499)
        url = url_object('http://w3af.org/a/b/foobar.php?foo=123')
        tag_value = createRandAlNum(10)
        for i in xrange(0, 500):
            fr = FuzzReq(url, dc={'a': ['1']})
            code = 200
            if i == find_id:
                code = 302
            res = httpResponse(code, '<html>',{'Content-Type':'text/html'}, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.setId(i)
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
        url = url_object('http://w3af.org/a/b/c.php')
        for i in xrange(0, 500):
            fr = FuzzReq(url, dc={'a': ['1']})
            res = httpResponse(200, '<html>',{'Content-Type':'text/html'}, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.setId(i)
            h1.response = res
            if i == mark_id:
                h1.toggleMark()
            h1.save()
        h2 = HistoryItem()
        h2.load(mark_id)
        self.assertTrue(h2.mark)

    def test_save_load(self):
        i = random.randint(1, 499)
        url = url_object('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        res = httpResponse(200, '<html>',{'Content-Type':'text/html'}, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.setId(i)
        h1.response = res
        h1.save()
        h2 = HistoryItem()
        h2.load(i)
        self.assertEqual(h1.request, h2.request)
        self.assertEqual(h1.response.body, h2.response.body)

    def test_delete(self):
        i = random.randint(1, 499)
        url = url_object('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        res = httpResponse(200, '<html>',{'Content-Type':'text/html'}, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.setId(i)
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
        url = url_object('http://w3af.com/a/b/c.php')
        fr = FuzzReq(url, dc={'a': ['1']})
        res = httpResponse(200, '<html>',{'Content-Type':'text/html'}, url, url)
        h1 = HistoryItem()
        h1.request = fr
        res.setId(i)
        h1.response = res
        h1.save()
        h1.clear()
        try:
            h2 = h1.read(i)
        except:
            h2 = None
        self.assertEqual(h2, None)
        self.assertFalse(os.path.exists(h1._sessionDir))

    def test_tag(self):
        tag_id = random.randint(501, 999)
        tag_value = createRandAlNum(10)
        url = url_object('http://w3af.org/a/b/c.php')

        for i in xrange(501, 1000):
            fr = FuzzReq(url, dc={'a': ['1']})
            res = httpResponse(200, '<html>',{'Content-Type':'text/html'}, url, url)
            h1 = HistoryItem()
            h1.request = fr
            res.setId(i)
            h1.response = res
            if i == tag_id:
                h1.updateTag(tag_value)
            h1.save()

        h2 = HistoryItem()
        h2.load(tag_id)
        self.assertEqual(h2.tag, tag_value)

if __name__ == '__main__':
    unittest.main(verbosity=2)
