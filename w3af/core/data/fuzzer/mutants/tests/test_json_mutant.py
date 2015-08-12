"""
test_json_mutant.py

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
import json
import copy

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.json_mutant import JSONMutant
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.tests.test_json_container import COMPLEX_OBJECT, ARRAY


class TestJSONMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {}
        self.payloads = ['xyz', 'www']
        self.url = URL('http://www.w3af.com/?id=3')

    def test_found_at(self):
        dc = JSONContainer(COMPLEX_OBJECT)
        freq = FuzzableRequest(self.url, post_data=dc, method='PUT')

        m = JSONMutant(freq)
        m.get_dc().set_token(('object-second_key-list-0-string',))

        expected = '"http://www.w3af.com/", using HTTP method PUT.'\
                   ' The sent JSON-data was: "...object-second_key-list-'\
                   '0-string=abc..."'
        self.assertEqual(m.found_at(), expected)

        headers = m.get_headers()
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')

    def test_create_mutants_array(self):
        dc = JSONContainer(ARRAY)
        freq = FuzzableRequest(self.url, post_data=dc, method='POST')

        created_mutants = JSONMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        expected_dcs = ['["xyz", 3, 2.1]',
                        '["www", 3, 2.1]']

        created_dcs = [str(i.get_dc()) for i in created_mutants]
        created_post_datas = [i.get_data() for i in created_mutants]

        self.assertEqual(set(created_dcs), set(expected_dcs))
        self.assertEqual(set(created_dcs), set(created_post_datas))

        token = created_mutants[0].get_token()
        self.assertEqual(token.get_name(), 'list-0-string')
        self.assertEqual(token.get_original_value(), 'abc')

        token = created_mutants[1].get_token()
        self.assertEqual(token.get_name(), 'list-0-string')
        self.assertEqual(token.get_original_value(), 'abc')

        for m in created_mutants:
            self.assertIsInstance(m, JSONMutant)

        for m in created_mutants:
            self.assertEqual(m.get_method(), 'POST')

    def test_create_mutants_9116(self):
        payment_data = {'transaction_amount': 100,
                        'reason': 'Title of what you are paying for',
                        'installments': 1,
                        'payment_method_id': 'visa',
                        'token': '16faba8617708',
                        'external_reference': '1234',
                        'random_anti_anti_double_click': 11577513359,
                        'extra_charge': None}
        payment_data = json.dumps(payment_data)

        dc = JSONContainer(payment_data)
        freq = FuzzableRequest(self.url, post_data=dc, method='POST')

        created_mutants = JSONMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        expected_dcs = ['{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "www", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "xyz", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "www", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "xyz", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "xyz", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "xyz", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "www", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "www", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": null}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": "xyz"}',
                        '{"transaction_amount": 100, "external_reference": "1234", "random_anti_anti_double_click": 11577513359, "token": "16faba8617708", "reason": "Title of what you are paying for", "installments": 1, "payment_method_id": "visa", "extra_charge": "www"}']

        created_dcs = [str(i.get_dc()) for i in created_mutants]
        created_post_datas = [i.get_data() for i in created_mutants]

        self.assertEqual(set(created_dcs), set(expected_dcs))
        self.assertEqual(set(created_dcs), set(created_post_datas))

        for m in created_mutants:
            m.set_token_value('abc')

    def test_create_mutants_empty_payload(self):
        dc = JSONContainer(COMPLEX_OBJECT)
        freq = FuzzableRequest(self.url, post_data=dc, method='POST')

        created_mutants = JSONMutant.create_mutants(freq, [''], [],
                                                    False, self.fuzzer_config)

        for m in created_mutants:
            m.set_token_value('abc')

    def test_mutant_copy_9116(self):
        dc = JSONContainer(COMPLEX_OBJECT)
        freq = FuzzableRequest(self.url, post_data=dc, method='POST')

        created_mutants = JSONMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        payload = 'def'

        m = created_mutants[0]

        dc = m.get_dc()
        dc_copy = copy.deepcopy(dc)
        self.assertEqual(dc_copy.get_token(), dc.get_token())

        mcopy = m.copy()
        token = mcopy.get_token()
        mcopy.set_token_value(payload)

        self.assertIsNotNone(m.get_token())
        self.assertIsNotNone(token)
        self.assertEqual(mcopy.get_token_value(), payload)
