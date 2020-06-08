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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.dc.utils.token import DataToken


class TestQSMutant(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {}

    def test_mutant_creation(self):
        self.url = URL('http://moth/?a=1&b=2')
        freq = FuzzableRequest(self.url)

        created_mutants = QSMutant.create_mutants(freq, self.payloads, [],
                                                  False, self.fuzzer_config)

        expected_dcs = ['a=abc&b=2', 'a=1&b=abc',
                        'a=def&b=2', 'a=1&b=def']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

        token_0 = created_mutants[0].get_token()
        self.assertIsInstance(token_0, DataToken)
        self.assertEqual(token_0.get_name(), 'a')
        self.assertEqual(token_0.get_original_value(), '1')
        self.assertEqual(token_0.get_value(), 'abc')

        token_2 = created_mutants[1].get_token()
        self.assertIsInstance(token_0, DataToken)
        self.assertEqual(token_2.get_name(), 'b')
        self.assertEqual(token_2.get_original_value(), '2')
        self.assertEqual(token_2.get_value(), 'abc')

        self.assertTrue(all(isinstance(m, QSMutant) for m in created_mutants))

    def test_mutant_creation_repeated_parameter_names(self):
        self.url = URL('http://moth/?id=1&id=2')
        freq = FuzzableRequest(self.url)

        created_mutants = QSMutant.create_mutants(freq, self.payloads, [],
                                                  False, self.fuzzer_config)

        expected_dcs = ['id=abc&id=2', 'id=1&id=abc',
                        'id=def&id=2', 'id=1&id=def']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

        token_0 = created_mutants[0].get_token()
        self.assertIsInstance(token_0, DataToken)
        self.assertEqual(token_0.get_name(), 'id')
        self.assertEqual(token_0.get_original_value(), '1')
        self.assertEqual(token_0.get_value(), 'abc')

        token_1 = created_mutants[1].get_token()
        self.assertIsInstance(token_1, DataToken)
        self.assertEqual(token_1.get_name(), 'id')
        self.assertEqual(token_1.get_original_value(), '2')
        self.assertEqual(token_1.get_value(), 'abc')

        self.assertTrue(all(isinstance(m, QSMutant) for m in created_mutants))
