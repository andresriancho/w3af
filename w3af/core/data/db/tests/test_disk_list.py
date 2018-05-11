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
import random
import string
import unittest
import threading
import itertools

import msgpack

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.db.dbms import get_default_temp_db_instance
from w3af.core.data.url.HTTPResponse import HTTPResponse


class TestDiskList(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    @attr('smoke')
    def test_int(self):
        dl = DiskList()

        for i in xrange(0, 1000):
            _ = dl.append(i)

        for i in xrange(0, 1000 / 2):
            r = random.randint(0, 1000 - 1)
            self.assertEqual(r in dl, True)

        for i in xrange(0, 1000 / 2):
            r = random.randint(1000, 1000 * 2)
            self.assertEqual(r in dl, False)

    def test_to_unicode(self):
        dl = DiskList()
        dl.append(1)
        dl.append(2)
        dl.append(3)
        
        self.assertEqual(unicode(dl), u'<DiskList [1, 2, 3]>')
            
    @attr('smoke')
    def test_string(self):
        dl = DiskList()

        for i in xrange(0, 1000):
            rnd = ''.join(random.choice(string.letters) for i in xrange(40))
            _ = dl.append(rnd)

        self.assertEqual(rnd in dl, True)

        for i in string.letters:
            self.assertNotIn(i, dl)

        self.assertIn(rnd, dl)

    def test_unicode(self):
        dl = DiskList()

        dl.append(u'à')
        dl.append(u'המלצת השבוע')
        dl.append([u'à', ])

        self.assertEqual(dl[0], u'à')
        self.assertEqual(dl[1], u'המלצת השבוע')
        self.assertEqual(dl[2], [u'à', ])

    @attr('smoke')
    def test_urlobject(self):
        dl = DiskList()

        dl.append(URL('http://w3af.org/?id=2'))
        dl.append(URL('http://w3af.org/?id=3'))

        self.assertEqual(dl[0], URL('http://w3af.org/?id=2'))
        self.assertEqual(dl[1], URL('http://w3af.org/?id=3'))
        self.assertNotIn(URL('http://w3af.org/?id=4'), dl)
        self.assertIn(URL('http://w3af.org/?id=2'), dl)

    def test_fuzzable_request(self):
        dl = DiskList()

        uri = URL('http://w3af.org/?id=2')
        qsr1 = FuzzableRequest(uri, method='GET', headers=Headers(
            [('Referer', 'http://w3af.org/')]))

        uri = URL('http://w3af.org/?id=3')
        qsr2 = FuzzableRequest(uri, method='OPTIONS', headers=Headers(
            [('Referer', 'http://w3af.org/')]))

        uri = URL('http://w3af.org/?id=7')
        qsr3 = FuzzableRequest(uri, method='FOO', headers=Headers(
            [('Referer', 'http://w3af.org/')]))

        dl.append(qsr1)
        dl.append(qsr2)

        self.assertEqual(dl[0], qsr1)
        self.assertEqual(dl[1], qsr2)
        self.assertFalse(qsr3 in dl)
        self.assertTrue(qsr2 in dl)

    def test_len(self):
        dl = DiskList()

        for i in xrange(0, 100):
            _ = dl.append(i)

        self.assertEqual(len(dl), 100)

    def test_pickle(self):
        dl = DiskList()

        dl.append('a')
        dl.append(1)
        dl.append([3, 2, 1])

        values = []
        for i in dl:
            values.append(i)

        self.assertEqual(values[0], 'a')
        self.assertEqual(values[1], 1)
        self.assertEqual(values[2], [3, 2, 1])

    def test_getitem(self):
        dl = DiskList()

        dl.append('a')
        dl.append(1)
        dl.append([3, 2, 1])

        self.assertEqual(dl[0], 'a')
        self.assertEqual(dl[1], 1)
        self.assertEqual(dl[2], [3, 2, 1])
        self.assertRaises(IndexError, dl.__getitem__, 3)
        
    def test_getitem_negative(self):
        dl = DiskList()

        dl.append('a')
        dl.append('b')
        dl.append('c')

        self.assertEqual(dl[-1], 'c')
        self.assertEqual(dl[-2], 'b')
        self.assertEqual(dl[-3], 'a')
        self.assertRaises(IndexError, dl.__getitem__, -4)
        
    def test_not(self):
        dl = DiskList()
        self.assertFalse(dl)

    def test_extend(self):
        dl = DiskList()

        dl.append('a')
        dl.extend([1, 2, 3])

        self.assertEqual(len(dl), 4)
        self.assertEqual(dl[0], 'a')
        self.assertEqual(dl[1], 1)
        self.assertEqual(dl[2], 2)
        self.assertEqual(dl[3], 3)

    def test_clear(self):
        dl = DiskList()

        dl.append('a')
        dl.append('b')

        self.assertEqual(len(dl), 2)

        dl.clear()

        self.assertEqual(len(dl), 0)

    def test_sorted(self):
        dl = DiskList()

        dl.append('abc')
        dl.append('def')
        dl.append('aaa')

        sorted_dl = sorted(dl)

        self.assertEqual(['aaa', 'abc', 'def'], sorted_dl)

    def test_ordered_iter(self):
        dl = DiskList()

        dl.append('abc')
        dl.append('def')
        dl.append('aaa')

        sorted_dl = []
        for i in dl.ordered_iter():
            sorted_dl.append(i)

        self.assertEqual(['aaa', 'abc', 'def'], sorted_dl)

    def test_reverse_iteration(self):
        dl = DiskList()
        dl.append(1)
        dl.append(2)
        dl.append(3)

        reverse_iter_res = []
        for i in reversed(dl):
            reverse_iter_res.append(i)

        self.assertEqual(reverse_iter_res, [3, 2, 1])

    def test_thread_safe(self):
        dl = DiskList()

        def worker(range_inst):
            for i in range_inst:
                dl.append(i)

        threads = []
        _min = 0
        for _max in xrange(0, 1100, 100):
            th = threading.Thread(target=worker, args=(xrange(_min, _max),))
            threads.append(th)
            _min = _max

        for th in threads:
            th.start()

        for th in threads:
            th.join()

        for i in xrange(0, 1000):
            self.assertTrue(i in dl, i)

        dl_as_list = list(dl)
        self.assertEqual(len(dl_as_list), len(set(dl_as_list)))

        dl_as_list.sort()
        self.assertEqual(dl_as_list, range(1000))

    def test_remove_table(self):
        disk_list = DiskList()
        table_name = disk_list.table_name
        db = get_default_temp_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        disk_list.cleanup()
        
        self.assertFalse(db.table_exists(table_name))

    def test_table_name_with_prefix(self):
        _unittest = 'unittest'
        disk_list = DiskList(_unittest)

        self.assertIn(_unittest, disk_list.table_name)
        db = get_default_temp_db_instance()

        self.assertTrue(db.table_exists(disk_list.table_name))

        disk_list.cleanup()

        self.assertFalse(db.table_exists(disk_list.table_name))

    def test_remove_table_then_add(self):
        disk_list = DiskList()
        disk_list.append(1)

        disk_list.cleanup()

        self.assertRaises(AssertionError, disk_list.append, 1)

    def test_islice(self):
        disk_list = DiskList()
        disk_list.extend('ABCDEFG')
        
        EXPECTED = 'CDEFG'
        result = ''
        
        for c in itertools.islice(disk_list, 2, None, None):
            result += c
        
        self.assertEqual(EXPECTED, result)
    
    def test_many_instances(self):
        all_instances = []
        amount = 200
        
        for _ in xrange(amount):
            disk_list = DiskList()
            all_instances.append(disk_list)
        
        self.assertEqual(len(all_instances), amount)
    
    def test_slice_all(self):
        disk_list = DiskList()
        disk_list.append('1')
        disk_list.append('2')
        
        dl_copy = disk_list[:]
        self.assertIn('1', dl_copy)
        self.assertIn('2', dl_copy)

    def test_slice_greater_than_length(self):
        disk_list = DiskList()
        disk_list.append('1')
        disk_list.append('2')

        dl_copy = disk_list[:50]
        self.assertIn('1', dl_copy)
        self.assertIn('2', dl_copy)
        self.assertEqual(2, len(dl_copy))

    def test_slice_first_N(self):
        disk_list = DiskList()
        disk_list.append('1')
        disk_list.append('2')
        disk_list.append('3')
        
        dl_copy = disk_list[:1]
        self.assertIn('1', dl_copy)
        self.assertNotIn('2', dl_copy)
        self.assertNotIn('3', dl_copy)

    def test_no_specific_serializer_with_string(self):
        #
        #   This test runs in ~5.1 seconds on my workstation
        #
        count = 30000
        dl = DiskList()

        for i in xrange(0, count):
            i_str = str(i)

            # This tests the serialization
            dl.append(i_str)

            # This tests the deserialization
            _ = dl[i]

    def test_specific_serializer_with_string(self):
        #
        #   This test runs in ~5.0 seconds on my workstation
        #
        #   It seems that cPickle takes almost no time to serialize
        #   a simple string.
        #
        count = 30000
        dl = DiskList(load=lambda x: x,
                      dump=lambda x: x)

        for i in xrange(0, count):
            i_str = str(i)

            # This tests the serialization
            dl.append(i_str)

            # This tests the deserialization
            _ = dl[i]

    def test_no_specific_serializer_with_http_response(self):
        #
        #   This test runs in 28.14 seconds on my workstation
        #
        body = '<html><a href="http://moth/abc.jsp">test</a></html>'
        headers = Headers([('Content-Type', 'text/html')])
        url = URL('http://w3af.com')
        response = HTTPResponse(200, body, headers, url, url, _id=1)

        count = 30000
        dl = DiskList()

        for i in xrange(0, count):
            # This tests the serialization
            dl.append(response)

            # This tests the deserialization
            _ = dl[i]

    def test_specific_serializer_with_http_response(self):
        #
        #   This test runs in 26.42 seconds on my workstation
        #
        body = '<html><a href="http://moth/abc.jsp">test</a></html>'
        headers = Headers([('Content-Type', 'text/html')])
        url = URL('http://w3af.com')
        response = HTTPResponse(200, body, headers, url, url, _id=1)

        def dump(http_response):
            return msgpack.dumps(http_response.to_dict(),
                                 use_bin_type=True)

        def load(serialized_object):
            data = msgpack.loads(serialized_object, raw=False)
            return HTTPResponse.from_dict(data)

        count = 30000
        dl = DiskList(dump=dump, load=load)

        for i in xrange(0, count):
            # This tests the serialization
            dl.append(response)

            # This tests the deserialization
            _ = dl[i]

