# -*- coding: utf-8 -*-
"""
test_query_string.py

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
import copy
import cPickle

from w3af.core.data.dc.query_string import QueryString


class TestQueryString(unittest.TestCase):

    def test_str_simple(self):
        self.assertEquals(str(QueryString([])), '')

    def test_str_with_equal(self):
        t1 = str(QueryString([('a', ['>']), ('b', ['a==1 && z >= 2', '3>2'])]))
        e1 = 'a=%3E&b=a%3D%3D1%20%26%26%20z%20%3E%3D%202&b=3%3E2'
        self.assertEqual(t1, e1)

        t2 = str(QueryString([('a', ['x=/etc/passwd'])]))
        e2 = 'a=x%3D%2Fetc%2Fpasswd'
        self.assertEqual(t2, e2)

    def test_str_with_double_quote(self):
        qs = str(QueryString([('a', ['1"2'])]))
        expected = 'a=1%222'
        self.assertEqual(qs, expected)

    def test_setitem_fail_on_string(self):
        qs = QueryString([('a', ['1'])])
        self.assertRaises(TypeError, qs.__setitem__, 'abc')

    def test_setitem_list(self):
        qs = QueryString([('a', ['1'])])
        qs['foo'] = ['bar']

        self.assertEqual(str(qs), 'a=1&foo=bar')

        qs['foo'] = ['bar', 'spam']
        self.assertEqual(str(qs), 'a=1&foo=bar&foo=spam')

    def test_copy_with_token(self):
        dc = QueryString([('a', ['1'])])

        dc.set_token(('a', 0))
        dc_copy = copy.deepcopy(dc)

        self.assertEqual(dc.get_token(), dc_copy.get_token())
        self.assertIsNotNone(dc.get_token())
        self.assertIsNotNone(dc_copy.get_token())
        self.assertEqual(dc_copy.get_token().get_name(), 'a')

    def test_pickle(self):
        dc = QueryString([('a', ['1'])])
        dc.set_token(('a', 0))

        pickled_qs = cPickle.dumps(dc)
        unpickled_qs = cPickle.loads(pickled_qs)

        self.assertEqual(dc, unpickled_qs)
        self.assertEqual(dc.keys(), unpickled_qs.keys())
        self.assertEqual(dc.keys(), ['a'])
        self.assertEqual(dc.get_token().get_name(), 'a')

    def test_encoding_special_unicode(self):
        qs = QueryString([('a', [u'✓'])])
        qs.set_token(('a', 0))

        self.assertEqual(str(qs), 'a=%E2%9C%93')

    def test_merge_two_qs(self):
        qs_1 = QueryString([('a', ['1'])])
        qs_2 = QueryString([('b', ['2'])])

        for key, values in qs_2.iteritems():
            qs_1[key] = values

        self.assertEqual(qs_1['b'], ['2'])
        self.assertEqual(qs_1['a'], ['1'])
