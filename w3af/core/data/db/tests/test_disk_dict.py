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
import time
import unittest

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.db.dbms import get_default_temp_db_instance


@attr('smoke')
class TestDiskDict(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_int(self):
        disk_dict = DiskDict()
        
        for i in xrange(100):
            disk_dict[i] = i
        
        # Do it twice to test that it works as expected (not creating a new)
        # row in the table, but modifying the value
        for i in xrange(100):
            disk_dict[i] = i
        
        self.assertEqual(len(disk_dict), 100)
        self.assertEqual(disk_dict[50], 50)
        self.assertIn(50, disk_dict)

    def test_not_in(self):
        disk_dict = DiskDict()

        self.assertRaises(KeyError, disk_dict.__getitem__, 'abc')

    def test_get(self):
        disk_dict = DiskDict()

        disk_dict[0] = 'abc'
        
        abc1 = disk_dict.get(0)
        abc2 = disk_dict.get(0, 1)
        two = disk_dict.get(1, 2)
        
        self.assertEqual(abc1, 'abc')
        self.assertEqual(abc2, 'abc')
        self.assertEqual(two, 2)

    def test_keys(self):
        disk_dict = DiskDict()

        disk_dict['a'] = 'abc'
        disk_dict['b'] = 'abc'
        disk_dict['c'] = 'abc'

        self.assertEqual(set(disk_dict.keys()), set(['a', 'b', 'c']))

    def test_del(self):
        disk_dict = DiskDict()
        disk_dict['a'] = 'abc'

        del disk_dict['a']
        self.assertNotIn('a', disk_dict)

    def test_len(self):
        disk_dict = DiskDict()
        disk_dict['a'] = 'abc'

        self.assertEqual(len(disk_dict), 1)

    def test_len_performance(self):
        disk_dict = DiskDict()

        for i in xrange(100000):
            disk_dict[i] = i

        start = time.time()

        for i in xrange(10000):
            len(disk_dict)

        end = time.time()

        self.assertLess(end - start, 10)

    def test_len_very_large_dict(self):
        disk_dict = DiskDict()

        items_to_add = 1000
        very_large_string = 'random_very_large_string' * 321

        for i in xrange(items_to_add):
            disk_dict[i] = very_large_string

        self.assertEqual(len(disk_dict), items_to_add)

    def test_iterkeys(self):
        disk_dict = DiskDict()

        disk_dict['a'] = 'abc'
        disk_dict['b'] = 'abc'
        disk_dict['c'] = 'abc'

        self.assertEqual(set(disk_dict.iterkeys()), set(['a', 'b', 'c']))

    def test_remove_table(self):
        disk_dict = DiskDict()
        table_name = disk_dict.table_name
        db = get_default_temp_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        disk_dict.cleanup()
        
        self.assertFalse(db.table_exists(table_name))

    def test_table_with_prefix(self):
        _unittest = 'unittest'
        disk_dict = DiskDict(_unittest)

        self.assertIn(_unittest, disk_dict.table_name)
        db = get_default_temp_db_instance()

        self.assertTrue(db.table_exists(disk_dict.table_name))

        disk_dict.cleanup()

        self.assertFalse(db.table_exists(disk_dict.table_name))