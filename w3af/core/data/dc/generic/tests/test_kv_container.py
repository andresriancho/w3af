# -*- coding: utf-8 -*-
"""
test_kv_container.py

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
import copy

from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.dc.utils.token import DataToken


class TestKeyValueContainer(unittest.TestCase):
    
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
        kv_setter = [(k, v, p, s) for (k, v, p, s) in dc.iter_setters()]

        EXPECTED_KEY_VALUES = [('a', '1', ('a', 0)),
                               ('b', '2', ('b', 0)),
                               ('b', '3', ('b', 1))]
        kvp = [(key, value, path) for (key, value, path, _) in kv_setter]
        self.assertEqual(EXPECTED_KEY_VALUES, kvp)

        for idx, (key, value, path, setter) in enumerate(kv_setter):
            if idx == 2:
                setter('w')

        self.assertEqual(str(dc), 'a=1&b=2&b=w')

        SET_VALUES = ['x', 'y', 'z']
        for idx, (key, value, path, setter) in enumerate(kv_setter):
            setter(SET_VALUES[idx])

        self.assertEqual(str(dc), 'a=x&b=y&b=z')

    def test_set_token(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        token = dc.set_token(('a', 0))
        self.assertEqual(token.get_name(), 'a')
        self.assertEqual(token, dc['a'][0])

    def test_copy_with_token(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        dc.set_token(('a', 0))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())

    def test_set_token_using_data_token(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        token = DataToken('a', '1', ('a', 0))
        set_token = dc.set_token(token)

        self.assertEqual(dc.get_token().get_name(), 'a')
        self.assertEqual(dc.get_token().get_value(), '1')
        self.assertEqual(dc.get_token().get_path(), ('a', 0))
        self.assertIs(dc.get_token(), token)
        self.assertIs(set_token, token)

    def test_is_variant_of_eq_keys_eq_value_types(self):
        dc1 = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dc2 = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        self.assertTrue(dc1.is_variant_of(dc2))

    def test_is_variant_of_neq_keys_eq_value_types(self):
        dc1 = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dc2 = KeyValueContainer([(u'a', ['1']), (u'c', ['2', '3'])])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_is_variant_of_neq_num_keys_eq_values(self):
        dc1 = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dc2 = KeyValueContainer([(u'a', ['1'])])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_is_variant_of_eq_keys_neq_value_types(self):
        dc1 = KeyValueContainer([(u'a', ['1']), (u'b', ['c', '3'])])
        dc2 = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_double_data_token_wrap(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['c', '3'])])
        dc.set_token(('b', 1))

        for dcc, token in dc.iter_bound_tokens():
            self.assertIsInstance(token, DataToken)
            self.assertIsInstance(token.get_value(), basestring)

    def test_double_data_token_wrap_set_set(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['c', '3'])])
        token_1 = dc.set_token(('b', 1))
        token_2 = dc.set_token(('b', 1))

        self.assertIs(token_1, token_2)

    def test_get_short_printable_repr(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dc.set_token(('a', 0))

        self.assertEqual(dc.get_short_printable_repr(), 'a=1&b=2&b=3')

    def test_get_short_printable_repr_token_obj_reduce_printable(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        dc.MAX_PRINTABLE = 5
        token = DataToken('a', '1', ('a', 0))
        dc.set_token(token)

        self.assertIsNotNone(dc.get_token())
        self.assertEqual(dc.get_short_printable_repr(), '...a=1...')

    def test_get_short_printable_repr_token_obj(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])
        token = DataToken('a', '1', ('a', 0))
        dc.set_token(token)

        self.assertIsNotNone(dc.get_token())
        self.assertEqual(dc.get_short_printable_repr(), 'a=1&b=2&b=3')

    def test_get_short_printable_repr_no_token(self):
        dc = KeyValueContainer([(u'a', ['1']), (u'b', ['2', '3'])])

        self.assertEqual(dc.get_short_printable_repr(), 'a=1&b=2&b=3')

    def test_get_short_printable_repr_unicode_value(self):
        dc = KeyValueContainer([(u'a', ['x']), (u'b', ['2', '3'])])
        dc.MAX_PRINTABLE = 5
        token = DataToken('a', 'é', ('a', 0))
        dc.set_token(token)

        self.assertEqual(dc.get_short_printable_repr(), '...a=....')

    def test_get_short_printable_repr_unicode_value_key(self):
        dc = KeyValueContainer([('aéb', ['céd']), (u'b', ['2', '3'])])
        dc.MAX_PRINTABLE = 7
        token = DataToken('aéb', 'céd', ('aéb', 0))
        dc.set_token(token)

        self.assertEqual(dc.get_short_printable_repr(), '...a.b=c.d...')

    def test_get_short_printable_repr_unicode_value_unicode(self):
        dc = KeyValueContainer([(u'aéb', [u'céd']), (u'b', ['2', '3'])])
        dc.MAX_PRINTABLE = 7
        token = DataToken(u'aéb', u'céd', (u'aéb', 0))
        dc.set_token(token)

        self.assertEqual(dc.get_short_printable_repr(), '...a.b=c.d...')
