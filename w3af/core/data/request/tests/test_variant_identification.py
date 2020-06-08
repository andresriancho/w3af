"""
test_variant_identification.py

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

from w3af.core.data.request.variant_identification import are_variants
from w3af.core.data.parsers.doc.url import URL


class TestVariantIdentification(unittest.TestCase):

    def test_eq(self):
        self.assertTrue(are_variants(URL('http://w3af.com/foo.php'),
                                     URL('http://w3af.com/foo.php')))

    def test_diff_params(self):
        self.assertFalse(are_variants(URL('http://w3af.com/foo.php?x=1'),
                                      URL('http://w3af.com/foo.php?y=1')))

    def test_diff_file_param(self):
        self.assertFalse(are_variants(URL('http://w3af.com/bar.php?id=1'),
                                      URL('http://w3af.com/foo.php?foo=1')))

    def test_diff_domain(self):
        self.assertFalse(are_variants(URL('http://w3af.com/foo.php?id=1'),
                                      URL('http://bonsai-sec.com/foo.php?id=1')))

    def test_diff_domain_params(self):
        self.assertFalse(
            are_variants(URL('http://w3af.com/foo.php?id=1&foo=bar'),
                         URL('http://w3af.org/foo.php?id=1')))

    def test_same_params_diff_values(self):
        self.assertTrue(
            are_variants(URL('http://w3af.com/foo.php?id=1&foo=bar'),
                         URL('http://w3af.com/foo.php?id=333&foo=spam')))

    def test_same_param_diff_value_type(self):
        self.assertFalse(are_variants(URL('http://w3af.com/foo.php?id=1111'),
                                      URL('http://w3af.com/foo.php?id=spam')))

    def test_raises(self):
        self.assertRaises(AttributeError, are_variants,
                          'http://w3af.com/foo.php?id=1',
                          'http://w3af.org/foo.php?id=1')
