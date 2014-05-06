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

from w3af.core.data.dc.query_string import QueryString


class TestQueryString(unittest.TestCase):

    def test_str_simple(self):
        self.assertEquals(str(QueryString([])), '')

    def test_str_with_equal(self):
        t1 = str(QueryString([('a','>'), ('b', ['a==1 && z >= 2','3>2'])]))
        e1 = 'a=%3E&b=a%3D%3D1%20%26%26%20z%20%3E%3D%202&b=3%3E2'
        self.assertEqual(t1, e1)

        t2 = str(QueryString([('a', 'x=/etc/passwd')]))
        e2 = 'a=x%3D%2Fetc%2Fpasswd'
        self.assertEqual(t2, e2)

