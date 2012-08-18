'''
httpResponse.py

Copyright 2012 Andres Riancho

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

from ..fuzzable_request import fuzzable_request as FuzzReq
from core.data.parsers.urlParser import url_object


class TestFuzzableRequest(unittest.TestCase):

    def setUp(self):
        self.url = url_object('http://w3af.com/a/b/c.php')
    
    def test_variants_commutative(self):
        # 'is_variant_of' is commutative
        fr = FuzzReq(self.url, method='POST', dc={'a': ['1']})
        fr_other = FuzzReq(self.url, method='POST', dc={'a': ['1']})
        self.assertTrue(fr.is_variant_of(fr_other))
        self.assertTrue(fr_other.is_variant_of(fr))

    def test_variants_false_diff_meths(self):
        # Different methods
        fr_get = FuzzReq(self.url, method='GET', dc={'a': ['1']})
        fr_post = FuzzReq(self.url, method='POST', dc={'a': ['1']})
        self.assertFalse(fr_get.is_variant_of(fr_post))
    
    def test_variants_false_diff_params_type(self):
        fr = FuzzReq(self.url, method='GET', dc={'a': ['1'], 'b': ['1']})
        fr_other = FuzzReq(self.url, method='GET', dc={'a': ['2'], 'b': ['cc']})
        self.assertFalse(fr.is_variant_of(fr_other))
    
    def test_variants_false_nonetype_in_params(self):
        fr = FuzzReq(self.url, method='GET', dc={'a': [None]})
        fr_other = FuzzReq(self.url, method='GET', dc={'a': ['s']})
        self.assertFalse(fr.is_variant_of(fr_other))
    
    def test_variants_true_similar_params(self):
        # change the url by adding a querystring. shouldn't affect anything.
        url = self.url.urlJoin('?a=z')
        fr = FuzzReq(url, method='GET', dc={'a': ['1'], 'b': ['bb']})
        fr_other = FuzzReq(self.url, method='GET', dc={'a': ['2'], 'b': ['cc']})
        self.assertTrue(fr.is_variant_of(fr_other))
    
    def test_variants_true_similar_params_two(self):
        fr = FuzzReq(self.url, method='GET', dc={'a':['b']})
        fr_other = FuzzReq(self.url, method='GET', dc={'a': ['']})
        self.assertTrue(fr.is_variant_of(fr_other))