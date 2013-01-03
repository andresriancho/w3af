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
import unittest
import string
import os

from itertools import repeat, starmap
from random import choice

from core.controllers.misc.temp_dir import (get_temp_dir, create_temp_dir,
                                            remove_temp_dir)
from core.data.db.db import DBClientSQLite


class TestDB(unittest.TestCase):
    
    def setUp(self):
        create_temp_dir()
    
    def tearDown(self):
        remove_temp_dir()
    
    def test_open_error(self):
        invalid_filename = '/'
        self.assertRaises(Exception, DBClientSQLite, invalid_filename)
    
    def test_simple_run(self):
        temp_dir = get_temp_dir()
        fname = ''.join(starmap(choice, repeat((string.letters,), 18)))
        filename = os.path.join(temp_dir, fname + '.w3af.temp_db')
                
        db = DBClientSQLite(filename)
        db.create_table('TEST', set([('id', 'INT'), ('data', 'TEXT')]))
        
        db.select('SELECT * from TEST')
        
    def test_close_twice(self):
        temp_dir = get_temp_dir()
        fname = ''.join(starmap(choice, repeat((string.letters,), 18)))
        filename = os.path.join(temp_dir, fname + '.w3af.temp_db')
                
        db = DBClientSQLite(filename)
        db.close()
        db.close()
