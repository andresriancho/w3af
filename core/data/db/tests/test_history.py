# -*- coding: UTF-8 -*-

import random
import unittest
import string
import time

from core.controllers.misc.temp_dir import create_temp_dir, remove_temp_dir
import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb
from core.data.db.history import HistoryItem

from core.data.request.fuzzableRequest import fuzzableRequest as FuzzReq
from core.data.url.httpResponse import httpResponse, DEFAULT_CHARSET
from core.data.parsers.urlParser import url_object

class TestHistoryItem(unittest.TestCase):
    # TODO
    # 1. add test for find()
    # 2. add test for delete()
    # 3. add test for clear()

    def setUp(self):
        cf.cf.save('sessionName',
                'defaultSession' + '-' + time.strftime('%Y-%b-%d_%H-%M-%S'))
        create_temp_dir()

    def tearDown(self):
        remove_temp_dir()

    def test_single_db(self):
        h1 = HistoryItem()
        h2 = HistoryItem()
        self.assertEqual(h1._db, h2._db)

    def test_save_load(self):
        i = 1002
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

    def test_mark(self):
        mark_id = 123
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

    def test_tag(self):
        tag_id = 567
        tag_value = 'Some tag'
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
    unittest.main()
