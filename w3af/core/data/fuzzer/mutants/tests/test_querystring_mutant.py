"""
test_querystring_mutant.py

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
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.dc.data_container import DataContainer


class TestQSMutant(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {}

    def test_print_mod_value(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'))
        m = QSMutant(freq)

        expected = 'The sent URI was http://www.w3af.com/?id=3 .'
        self.assertEqual(m.print_mod_value(), expected)

    def test_mutant_creation(self):
        self.url = URL('http://moth/?a=1&b=2')
        freq = HTTPQSRequest(self.url)

        created_mutants = QSMutant.create_mutants(freq, self.payloads, [],
                                                  False, self.fuzzer_config)

        expected_dc_lst = [DataContainer([('a', ['abc']), ('b', ['2'])]),
                           DataContainer([('a', ['def']), ('b', ['2'])]),
                           DataContainer([('a', ['1']), ('b', ['abc'])]),
                           DataContainer([('a', ['1']), ('b', ['def'])])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

        self.assertEqual(created_mutants[0].get_var(), 'a')
        self.assertEqual(created_mutants[0].get_var_index(), 0)
        self.assertEqual(created_mutants[0].get_original_value(), '1')
        self.assertEqual(created_mutants[2].get_var(), 'b')
        self.assertEqual(created_mutants[2].get_var_index(), 0)
        self.assertEqual(created_mutants[2].get_original_value(), '2')

        self.assertTrue(all(isinstance(m, QSMutant) for m in created_mutants))

    def test_mutant_creation_repeated_parameter_names(self):
        self.url = URL('http://moth/?id=1&id=2')
        freq = HTTPQSRequest(self.url)

        created_mutants = QSMutant.create_mutants(freq, self.payloads, [],
                                                  False, self.fuzzer_config)

        expected_dc_lst = [DataContainer([('id', ['abc', '2'])]),
                           DataContainer([('id', ['def', '2'])]),
                           DataContainer([('id', ['1', 'abc'])]),
                           DataContainer([('id', ['1', 'def'])])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

        self.assertEqual(created_mutants[0].get_var(), 'id')
        self.assertEqual(created_mutants[0].get_var_index(), 0)
        self.assertEqual(created_mutants[0].get_original_value(), '1')

        self.assertEqual(created_mutants[2].get_var(), 'id')
        self.assertEqual(created_mutants[2].get_var_index(), 1)
        self.assertEqual(created_mutants[2].get_original_value(), '2')

        self.assertTrue(all(isinstance(m, QSMutant) for m in created_mutants))
