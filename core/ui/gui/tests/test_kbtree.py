'''
test_kbtree.py

Copyright 2011 Andres Riancho

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
'''
import unittest
import gtk

from mock import Mock

from core.ui.gui.kb.kbtree import KBTree
from core.data.kb.knowledge_base import kb
from core.data.kb.info import Info
from core.data.kb.vuln import Vuln


class TestKBTree(unittest.TestCase):
    def setUp(self):
        long_desc = 'Foo bar spam eggs' * 10
        i = Info('TestCase', long_desc, 1, 'plugin_name')
        v = Vuln('TestCase', long_desc, 'Medium', 1, 'plugin_name')
        
        kb.append('a', 'b', i)
        kb.append('a', 'b', v)
    
    def tearDown(self):
        kb.clear('a', 'b')
        
    def test_kb_tree_basics(self):
        w3af = Mock()
        type_filter = {'info': True, 'vuln': True}
        
        kbtree = KBTree(w3af, type_filter, 'Title', True)
        
        filtered_kb = kbtree._filterKB()
        self.assertIn('a', filtered_kb)
        self.assertIn('b', filtered_kb['a'][0])
        
