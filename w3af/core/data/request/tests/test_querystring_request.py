# -*- coding: utf-8 -*-
"""
test_querystring_request.py

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

from nose.plugins.attrib import attr

from w3af.core.data.request.querystring_request import HTTPQSRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.query_string import QueryString


@attr('smoke')
class TestHTTPQSRequest(unittest.TestCase):

    def get_url(self):
        return URL('http://w3af.com/a/b/c.php')

    def test_variants_commutative(self):
        # 'is_variant_of' is commutative
        fr1 = HTTPQSRequest(self.get_url(), method='GET')
        fr1.set_dc(QueryString([('a', ['1', 'xx'])]))

        fr2 = HTTPQSRequest(self.get_url(), method='GET')
        fr2.set_dc(QueryString([('a', ['2', 'yy'])]))

        self.assertTrue(fr1.is_variant_of(fr2))
        self.assertTrue(fr2.is_variant_of(fr1))

    def test_variants_false_diff_meths(self):
        # Different methods
        fr1 = HTTPQSRequest(self.get_url(), method='POST')
        fr1.set_dc(QueryString([('a', ['1'])]))

        fr2 = HTTPQSRequest(self.get_url(), method='GET')
        fr2.set_dc(QueryString([('a', ['1'])]))

        self.assertFalse(fr1.is_variant_of(fr2))
        self.assertFalse(fr2.is_variant_of(fr1))

    def test_variants_false_diff_params_type(self):
        fr1 = HTTPQSRequest(self.get_url())
        fr1.set_dc(QueryString([('a', ['1'])]))

        fr2 = HTTPQSRequest(self.get_url())
        fr2.set_dc(QueryString([('a', ['cc'])]))

        self.assertFalse(fr1.is_variant_of(fr2))
        self.assertFalse(fr2.is_variant_of(fr1))

    def test_variants_false_different_url(self):
        fr1 = HTTPQSRequest(URL('http://w3af.com/a/b/c.php'))
        fr1.set_dc(QueryString([('a', ['1'])]))

        fr2 = HTTPQSRequest(URL('http://w3af.com/x/y/z.php'))
        fr2.set_dc(QueryString([('a', [''])]))

        self.assertFalse(fr1.is_variant_of(fr2))
        self.assertFalse(fr2.is_variant_of(fr1))

    def test_variants_true_similar_params_two(self):
        fr1 = HTTPQSRequest(self.get_url())
        fr1.set_dc(QueryString([('a', ['b'])]))

        fr2 = HTTPQSRequest(self.get_url())
        fr2.set_dc(QueryString([('a', [''])]))

        self.assertTrue(fr1.is_variant_of(fr2))
        self.assertTrue(fr2.is_variant_of(fr1))