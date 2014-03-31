# -*- coding: UTF-8 -*-
"""
Copyright 2013 Andres Riancho

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
import unittest
import string
import os

from itertools import repeat, starmap
from random import choice

from w3af.core.controllers.exceptions import DBException
from w3af.core.controllers.misc.temp_dir import (get_temp_dir, create_temp_dir,
                                            remove_temp_dir)
from w3af.core.data.db.dbms import SQLiteDBMS, get_default_temp_db_instance


def get_temp_filename():
    temp_dir = get_temp_dir()
    fname = ''.join(starmap(choice, repeat((string.letters,), 18)))
    filename = os.path.join(temp_dir, fname + '.w3af.temp_db')
    return filename

class TestDBMS(unittest.TestCase):
    
    def setUp(self):
        create_temp_dir()
    
    def tearDown(self):
        remove_temp_dir()
    
    def test_open_error(self):
        invalid_filename = '/'
        self.assertRaises(DBException, SQLiteDBMS, invalid_filename)
    
    def test_simple_db(self):
        db = SQLiteDBMS(get_temp_filename())
        db.create_table('TEST', set([('id', 'INT'), ('data', 'TEXT')])).result()
        
        db.execute('INSERT INTO TEST VALUES (1,"a")').result()
        
        self.assertIn( ('1', 'a'), db.select('SELECT * from TEST'))
        self.assertEqual( ('1', 'a'), db.select_one('SELECT * from TEST'))

    def test_default_db(self):
        db = get_default_temp_db_instance()
        db.create_table('TEST', set([('id', 'INT'), ('data', 'TEXT')])).result()
        
        db.execute('INSERT INTO TEST VALUES (1,"a")').result()
        
        self.assertIn( ('1', 'a'), db.select('SELECT * from TEST'))
        self.assertEqual( ('1', 'a'), db.select_one('SELECT * from TEST'))

    def test_simple_db_with_pk(self):
        db = SQLiteDBMS(get_temp_filename())
        fr = db.create_table('TEST', [('id', 'INT'), ('data', 'TEXT')],['id'])
        fr.result()
        
        self.assertEqual([], db.select('SELECT * from TEST'))
    
    def test_drop_table(self):
        db = SQLiteDBMS(get_temp_filename())
        fr = db.create_table('TEST', [('id', 'INT'), ('data', 'TEXT')],['id'])
        fr.result()
        
        db.drop_table('TEST').result()
        self.assertRaises(DBException, db.drop_table('TEST').result)
    
    def test_simple_db_with_index(self):
        db = SQLiteDBMS(get_temp_filename())
        fr = db.create_table('TEST', [('id', 'INT'), ('data', 'TEXT')],['id'])
        fr.result()
        
        db.create_index('TEST', ['data']).result()
        self.assertRaises(DBException,
                          db.create_index('TEST', ['data']).result)
    
    def test_table_exists(self):
        db = SQLiteDBMS(get_temp_filename())
        self.assertFalse(db.table_exists('TEST'))
        
        db = SQLiteDBMS(get_temp_filename())
        db.create_table('TEST', [('id', 'INT'), ('data', 'TEXT')],['id'])
        
        self.assertTrue(db.table_exists('TEST'))
    
    def test_close_twice(self):
        db = SQLiteDBMS(get_temp_filename())
        db.close()
        db.close()

class TestDefaultDB(unittest.TestCase):
    def test_get_default_temp_db_instance(self):
        self.assertEqual(id(get_default_temp_db_instance()),
                         id(get_default_temp_db_instance()))    