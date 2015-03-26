# -*- coding: utf-8 -*-
"""
test_nr_kv_container.py

Copyright 2014 Andres Riancho

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

from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


class TestNoRepeatKeyValueContainer(unittest.TestCase):

    def test_basic(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])

        self.assertIn('a', dc)
        self.assertIn('b', dc)

        self.assertEqual(dc['a'], '1')
        self.assertEqual(dc['b'], '2')

    def test_str(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        str_dc = str(dc)
        self.assertEqual(str_dc, 'a=1&b=2')
        self.assertIsInstance(str_dc, str)

        dc = NonRepeatKeyValueContainer([(u'a', u'')])
        self.assertEqual(str(dc), 'a=')

    def test_str_special_chars(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'Ú-ú-Ü-ü')], 'latin-1')
        decoded_str = urllib.unquote(str(dc)).decode('latin-1')
        self.assertEquals(u'a=Ú-ú-Ü-ü', decoded_str)

    def test_unicode(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        udc = unicode(dc)

        self.assertEqual(udc, u'a=1&b=2')
        self.assertIsInstance(udc, unicode)

    def test_iter_tokens(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        tokens = [t for t in dc.iter_tokens()]

        EXPECTED_TOKENS = [('a', '1'), ('b', '2')]
        token_data = [(t.get_name(), t.get_value()) for t in tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

    def test_iter_bound_tokens(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        dcc_tokens = [(dcc, t) for dcc, t in dc.iter_bound_tokens()]

        EXPECTED_TOKENS = [('a', '1'), ('b', '2')]
        token_data = [(t.get_name(), t.get_value()) for dcc, t in dcc_tokens]
        self.assertEqual(EXPECTED_TOKENS, token_data)

        for dcc, _ in dcc_tokens:
            self.assertIsInstance(dcc, NonRepeatKeyValueContainer)
            self.assertEquals(dcc, dc)

        self.assertEqual(str(dcc), 'a=1&b=2')

        only_dcc = [dcc for dcc, t in dcc_tokens]
        dcc = only_dcc[0]
        token = dcc.get_token()
        token.set_value('5')
        self.assertEqual(str(dcc), 'a=5&b=2')

        dcc = only_dcc[1]
        token = dcc.get_token()
        token.set_value('5')
        self.assertEqual(str(dcc), 'a=1&b=5')

    def test_iter_setters(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        kv_setter = [(k, v, p, s) for (k, v, p, s) in dc.iter_setters()]

        EXPECTED_KEY_VALUES = [('a', '1', ('a',)), ('b', '2', ('b',))]
        kvp = [(key, value, path) for (key, value, path, _) in kv_setter]
        self.assertEqual(EXPECTED_KEY_VALUES, kvp)

        for idx, (key, value, path, setter) in enumerate(kv_setter):
            if idx == 1:
                setter('w')

        self.assertEqual(str(dc), 'a=1&b=w')

        SET_VALUES = ['x', 'y']
        for idx, (key, value, path, setter) in enumerate(kv_setter):
            setter(SET_VALUES[idx])

        self.assertEqual(str(dc), 'a=x&b=y')

    def test_set_token(self):
        dc = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])

        token = dc.set_token(('b',))
        self.assertEqual(token.get_name(), 'b')
        self.assertEqual(token, dc['b'])

    def test_is_variant_of_eq_keys_eq_value_types(self):
        dc1 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        dc2 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])

        self.assertTrue(dc1.is_variant_of(dc2))

    def test_is_variant_of_neq_keys_eq_value_types(self):
        dc1 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        dc2 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'c', u'2')])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_is_variant_of_neq_num_keys_eq_values(self):
        dc1 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        dc2 = NonRepeatKeyValueContainer([(u'a', u'1')])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_is_variant_of_eq_keys_neq_value_types(self):
        dc1 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'2')])
        dc2 = NonRepeatKeyValueContainer([(u'a', u'1'), (u'b', u'cc')])

        self.assertFalse(dc1.is_variant_of(dc2))

    def test_copy_with_token(self):
        dc = NonRepeatKeyValueContainer([(u'a', '1'), (u'b', '2')])

        dc.set_token(('a',))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())