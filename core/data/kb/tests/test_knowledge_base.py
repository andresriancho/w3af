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

from core.data.kb.knowledgeBase import kb

class test_knowledge_base(unittest.TestCase):
    
    def setUp(self):
        kb.cleanup()
    
    def test_basic(self):
        kb.save('a','b','c')
        data = kb.get('a','b')
        self.assertEqual(data, 'c')
    
    def test_default(self):
        self.assertEqual( kb.get('a','b'), [] )
    
    def test_default_first_saved(self):
        kb.save('a', 'b', 'c')
        self.assertEqual( kb.get('a','not-exist'), [] )
    
    def test_return_all_for_plugin(self):
        kb.append('a', 'b', 'c')
        kb.append('a', 'b', 'd')
        kb.append('a', 'b', 'e')
        self.assertEqual( kb.get('a'), {'b': ['c', 'd', 'e']})
    
    def test_append(self):
        kb.append('a', 'b', 1)
        kb.append('a', 'b', 2)
        kb.append('a', 'b', 3)
        self.assertEqual( kb.get('a', 'b'), [1,2,3] )
    
    def test_append_save(self):
        kb.append('a', 'b', 1)
        kb.append('a', 'b', 2)
        kb.save('a', 'b', 3)
        self.assertEqual( kb.get('a', 'b'), 3 )
    
    def test_save_append(self):
        kb.save('a', 'b', [1,])
        kb.append('a', 'b', 2)
        kb.append('a', 'b', 3)
        self.assertEqual( kb.get('a', 'b'), [1,2,3] )
    
    def test_all_of_klass(self):
        kb.save('a', 'b', [1,])
        self.assertEqual( kb.getAllEntriesOfClass(int), [1])

    def test_all_of_klass_str(self):
        kb.append('a', 'b', 'abc')
        self.assertEqual( kb.getAllEntriesOfClass(str), ['abc'])
    
    def test_dump_empty(self):
        empty = kb.dump()
        self.assertEqual(empty, {})
        
    def test_dump(self):
        kb.save('a', 'b', [1,])
        self.assertEqual(kb.dump(), {'a': {'b': [1]}})
        
        