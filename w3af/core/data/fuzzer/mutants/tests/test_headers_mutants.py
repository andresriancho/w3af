"""
test_headers_mutant.py

Copyright 2006 Andres Riancho

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

from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.request.HTTPQsRequest import HTTPQSRequest
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.dc.headers import Headers


class TestHeadersMutant(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {}
        self.fuzzer_config['fuzzable_headers'] = ['Referer']

    def test_basic(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/'))
        fake_ref = 'http://w3af.org/'

        mutant = HeadersMutant(freq.copy())
        mutant.set_var('Referer')
        original_referer = freq.get_referer()
        mutant.set_original_value(original_referer)
        mutant.set_mod_value(fake_ref)

        self.assertEqual(mutant.get_headers()['Referer'], fake_ref)
        self.assertEqual(mutant.get_original_value(), original_referer)

    def test_found_at(self):
        headers = Headers([('Referer', 'http://moth/')])
        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'),
                               headers=headers)
        m = HeadersMutant(freq)
        m.set_var('Referer')
        m.set_mod_value('foo')

        expected = '"http://www.w3af.com/", using HTTP method GET. The modified'\
                   ' header was: "Referer" and it\'s value was: "foo".'
        self.assertEqual(m.found_at(), expected)

    def test_mutant_creation(self):
        url = URL('http://moth/?a=1&b=2')
        headers = Headers([('Referer', 'http://moth/')])
        freq = HTTPQSRequest(url, headers=headers)

        created_mutants = HeadersMutant.create_mutants(freq, self.payloads, [],
                                                       False, self.fuzzer_config)

        expected_dc_lst = [Headers([('Referer', 'abc')]),
                           Headers([('Referer', 'def')])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

        self.assertEqual(created_mutants[0].get_var(), 'Referer')
        self.assertEqual(created_mutants[0].get_var_index(), 0)
        self.assertEqual(created_mutants[0].get_original_value(), '')
        self.assertEqual(created_mutants[1].get_var(), 'Referer')
        self.assertEqual(created_mutants[1].get_var_index(), 0)
        self.assertEqual(created_mutants[1].get_original_value(), '')

        self.assertTrue(
            all(isinstance(m, HeadersMutant) for m in created_mutants))
