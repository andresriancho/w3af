'''
test_knowledge_base.py

Copyright 2006 Andres Riancho

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

from core.data.parsers.url import URL
from core.data.kb.knowledge_base import kb
from core.data.kb.tests.test_info import MockInfo
from core.data.dc.queryString import QueryString


class TestKnowledgeBase(unittest.TestCase):

    def setUp(self):
        kb.cleanup()

    def test_basic(self):
        kb.raw_write('a', 'b', 'c')
        data = kb.raw_read('a', 'b')
        self.assertEqual(data, 'c')

    def test_default_get(self):
        self.assertEqual(kb.get('a', 'b'), [])
    
    def test_default_raw_read(self):
        self.assertEqual(kb.raw_read('a', 'b'), [])

    def test_raw_read_error(self):
        kb.append('a', 'b', MockInfo())
        kb.append('a', 'b', MockInfo())
        self.assertRaises(RuntimeError, kb.raw_read,'a', 'b')

    def test_default_first_saved(self):
        kb.raw_write('a', 'b', 'c')
        self.assertEqual(kb.get('a', 'not-exist'), [])
        self.assertEqual(kb.raw_read('a', 'not-exist'), [])

    def test_return_all_for_plugin(self):
        i1 = MockInfo()
        i2 = MockInfo()
        i3 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        kb.append('a', 'b', i3)
        
        self.assertEqual(kb.get('a', 'b'), [i1, i2, i3])

    def test_append(self):
        i1 = MockInfo()
        i2 = MockInfo()
        i3 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        kb.append('a', 'b', i3)
        
        self.assertEqual(kb.get('a', 'b'), [i1, i1, i1, i2, i3])

    def test_append_uniq_var_default(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, ])

    def test_append_uniq_var_specific(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1, filter_by='VAR')
        kb.append_uniq('a', 'b', i2, filter_by='VAR')
        self.assertEqual(kb.get('a', 'b'), [i1, ])

    def test_append_uniq_var_bug_10Dec2012(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html'))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html'))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, ])
        
    def test_append_uniq_var_not_uniq(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/def.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_append_uniq_url_uniq(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1, filter_by='URL')
        kb.append_uniq('a', 'b', i2, filter_by='URL')
        self.assertEqual(kb.get('a', 'b'), [i1,])

    def test_append_uniq_url_different(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/def.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1, filter_by='URL')
        kb.append_uniq('a', 'b', i2, filter_by='URL')
        self.assertEqual(kb.get('a', 'b'), [i1, i2])
        
    def test_append_save(self):
        i1 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.raw_write('a', 'b', 3)
        
        self.assertEqual(kb.raw_read('a', 'b'), 3)

    def test_save_append(self):
        '''
        Although calling raw_write and then append is highly discouraged,
        someone would want to use it.
        '''
        kb.raw_write('a', 'b', 1)
        
        i1 = MockInfo()
        i2 = MockInfo()
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        
        self.assertEqual(kb.get('a', 'b'), [1, i1, i2])

    def test_all_of_klass(self):
        kb.raw_write('a', 'b', 1)
        self.assertEqual(kb.get_all_entries_of_class(int), [1])

    def test_all_of_klass_str(self):
        kb.raw_write('a', 'b', 'abc')
        self.assertEqual(kb.get_all_entries_of_class(str), ['abc'])

    def test_dump_empty(self):
        empty = kb.dump()
        self.assertEqual(empty, {})

    def test_dump(self):
        kb.raw_write('a', 'b', 1)
        self.assertEqual(kb.dump(), {'a': {'b': [1]}})

    def test_clear(self):
        kb.raw_write('a', 'b', 'abc')
        kb.raw_write('a', 'c', 'abc')
        kb.clear('a', 'b')
        self.assertEqual(kb.raw_read('a', 'b'), [])
        self.assertEqual(kb.raw_read('a', 'c'), 'abc')

    def test_overwrite(self):
        kb.raw_write('a', 'b', 'abc')
        kb.raw_write('a', 'b', 'def')
        self.assertEqual(kb.raw_read('a', 'b'), 'def')
