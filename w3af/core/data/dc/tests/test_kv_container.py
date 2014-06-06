# -*- coding: utf-8 -*-
"""
test_data_container.py

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
import unittest
import urllib

from w3af.core.data.dc.kv_container import KeyValueContainer


class TestDataContainer(unittest.TestCase):
    
    def test_basic(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        
        self.assertIn('a', dc)
        self.assertIn('b', dc)
        
        self.assertEqual(dc['a'], ['1'])
        self.assertEqual(dc['b'], ['2', '3'])
    
    def test_str(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2','3'])])
        str_dc = str(dc)
        self.assertEqual(str_dc, 'a=1&b=2&b=3')
        self.assertIsInstance(str_dc, str) 
        
        dc = KeyValueContainer([(u'aaa', [''])])
        self.assertEqual(str(dc), 'aaa=')
        
        dc = KeyValueContainer([(u'aaa', ('', ''))])
        self.assertEqual(str(dc), 'aaa=&aaa=')
    
    def test_str_special_chars(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'u', [u'Ú-ú-Ü-ü'])], 'latin1')
        decoded_str = urllib.unquote(str(dc)).decode('latin-1')
        self.assertEquals(u'a=1&u=Ú-ú-Ü-ü', decoded_str)
        
    def test_unicode(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', u'3'])])
        udc = unicode(dc)
        
        self.assertEqual(udc, u'a=1&b=2&b=3')
        self.assertIsInstance(udc, unicode)

    def test_iter_tokens(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        tokens = [t for t in dc.iter_tokens()]

        EXPECTED_TOKENS = [('a', '1'), ('b', '2'), ('b', '3')]
        token_data = [(t.get_name(), t.get_value()) for t in tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_iter_bound_tokens(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dcc_tokens = [(dcc, t) for dcc, t in dc.iter_bound_tokens()]

        EXPECTED_TOKENS = [('a', '1'), ('b', '2'), ('b', '3')]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

        for dcc, _ in dcc_tokens:
            self.assertIsInstance(dcc, KeyValueContainer)
            self.assertEquals(dcc, dc)

        self.assertEqual(str(dcc), 'a=1&b=2&b=3')

        only_dcc = [dcc for dcc, t in dcc_tokens]
        dcc = only_dcc[0]
        token = dcc.get_token()
        token.set_value('5')
        self.assertEqual(str(dcc), 'a=5&b=2&b=3')

        dcc = only_dcc[1]
        token = dcc.get_token()
        token.set_value('5')
        self.assertEqual(str(dcc), 'a=1&b=5&b=3')

        dcc = only_dcc[2]
        token = dcc.get_token()
        token.set_value('5')
        self.assertEqual(str(dcc), 'a=1&b=2&b=5')

    def test_iter_setters(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        kv_setter = [(key, value, setter) for key, value, setter in dc.iter_setters()]

        EXPECTED_KEY_VALUES = [('a', '1'), ('b', '2'), ('b', '3')]
        self.assertEqual(EXPECTED_KEY_VALUES,
                         [(key, value) for (key, value, _) in kv_setter])

        for idx, (key, value, setter) in enumerate(kv_setter):
            if idx == 2:
                setter('w')

        self.assertEqual(str(dc), 'a=1&b=2&b=w')

        SET_VALUES = ['x', 'y', 'z']
        for idx, (key, value, setter) in enumerate(kv_setter):
            setter(SET_VALUES[idx])

        self.assertEqual(str(dc), 'a=x&b=y&b=z')