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
from core.data.kb.info import info
from core.data.dc.queryString import QueryString


class test_knowledge_base(unittest.TestCase):

    def setUp(self):
        kb.cleanup()

    def test_basic(self):
        kb.save('a', 'b', 'c')
        data = kb.get('a', 'b')
        self.assertEqual(data, 'c')

    def test_default(self):
        self.assertEqual(kb.get('a', 'b'), [])

    def test_default_first_saved(self):
        kb.save('a', 'b', 'c')
        self.assertEqual(kb.get('a', 'not-exist'), [])

    def test_return_all_for_plugin(self):
        kb.append('a', 'b', 'c')
        kb.append('a', 'b', 'd')
        kb.append('a', 'b', 'e')
        self.assertEqual(kb.get('a'), {'b': ['c', 'd', 'e']})

    def test_append(self):
        kb.append('a', 'b', 1)
        kb.append('a', 'b', 2)
        kb.append('a', 'b', 3)
        self.assertEqual(kb.get('a', 'b'), [1, 2, 3])

    def test_append_uniq_true(self):
        i1 = info()
        i1.setURI(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = info()
        i2.setURI(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, ])

    def test_append_uniq_false(self):
        i1 = info()
        i1.setURI(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', '1')]))
        i1.set_var('id')

        i2 = info()
        i2.setURI(URL('http://moth/def.html?id=3'))
        i2.set_dc(QueryString([('id', '3')]))
        i2.set_var('id')

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_append_save(self):
        kb.append('a', 'b', 1)
        kb.append('a', 'b', 2)
        kb.save('a', 'b', 3)
        self.assertEqual(kb.get('a', 'b'), 3)

    def test_save_append(self):
        kb.save('a', 'b', [1, ])
        kb.append('a', 'b', 2)
        kb.append('a', 'b', 3)
        self.assertEqual(kb.get('a', 'b'), [1, 2, 3])

    def test_all_of_klass(self):
        kb.save('a', 'b', [1, ])
        self.assertEqual(kb.getAllEntriesOfClass(int), [1])

    def test_all_of_klass_str(self):
        kb.append('a', 'b', 'abc')
        self.assertEqual(kb.getAllEntriesOfClass(str), ['abc'])

    def test_dump_empty(self):
        empty = kb.dump()
        self.assertEqual(empty, {})

    def test_dump(self):
        kb.save('a', 'b', [1, ])
        self.assertEqual(kb.dump(), {'a': {'b': [1]}})
