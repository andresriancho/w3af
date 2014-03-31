"""
test_mutant.py

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

from w3af.core.data.fuzzer.mutants.mutant import Mutant, mutant_smart_fill
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.dc.form import Form


class TestMutant(unittest.TestCase):

    def setUp(self):
        self.dc = DataContainer()
        self.url = URL('http://moth/')
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {}
        self.fuzzer_config['fuzz_form_files'] = 'gif'

    def test_mutant_creation(self):
        self.dc['a'] = ['1', ]
        self.dc['b'] = ['2', ]
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
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

        self.assertTrue(all(isinstance(m, Mutant) for m in created_mutants))
        self.assertTrue(all(m.get_mutant_class() == 'Mutant' for m in created_mutants))

    def test_get_mutant_class(self):
        m = Mutant(None)
        self.assertEqual(m.get_mutant_class(), 'Mutant')
        
    def test_mutant_generic_methods(self):
        self.dc['a'] = ['1', ]
        self.dc['b'] = ['2', ]
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                False, self.fuzzer_config)

        mutant = created_mutants[0]

        self.assertEqual(
            repr(mutant), '<mutant-generic | GET | http://moth/ >')
        self.assertEqual(
            mutant.print_mod_value(), 'The data that was sent is: "None".')
        self.assertNotEqual(id(mutant.copy()), id(mutant))

        self.assertRaises(ValueError, mutant.get_original_response_body)

        body = 'abcdef123'
        mutant.set_original_response_body(body)
        self.assertEqual(mutant.get_original_response_body(), body)

    def test_mutant_creation_ignore_params(self):
        self.dc['a'] = ['1', ]
        self.dc['b'] = ['2', ]
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, ['a', ],
                                                False, self.fuzzer_config)

        expected_dc_lst = [DataContainer([('a', ['abc']), ('b', ['2'])]),
                           DataContainer([('a', ['def']), ('b', ['2'])])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_mutant_creation_empty_dc(self):
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                False, self.fuzzer_config)

        expected_dc_lst = []
        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_mutant_creation_post_data(self):
        original_form = Form()
        original_form.add_input([("name", "username"), ("value", "")])
        original_form.add_input([("name", "address"), ("value", "")])
        original_form.add_file_input([("name", "file"), ("type", "file")])

        freq = HTTPPostDataRequest(self.url, dc=original_form)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                False, self.fuzzer_config)

        self.assertEqual(len(created_mutants), 4, created_mutants)

        expected_username_values = self.payloads + ['John8212'] * 2
        expected_address_values = ['Bonsai Street 123'] * 2 + self.payloads
        expected_file_values = ['GIF89a'] * 4

        created_dc_lst = [i.get_dc() for i in created_mutants]
        generated_username_values = [dc['username'][0]
                                     for dc in created_dc_lst]
        generated_address_values = [dc['address'][0] for dc in created_dc_lst]
        generated_file_values = [dc['file'][0] for dc in created_dc_lst]

        self.assertEqual(expected_username_values, generated_username_values)
        self.assertEqual(expected_address_values, generated_address_values)
        for index, gen_file_value in enumerate(generated_file_values):
            startswith = gen_file_value.startswith(expected_file_values[index])
            self.assertTrue(startswith, gen_file_value)

        self.assertTrue(all(str_file.name[-4:].startswith('.gif') for
                            str_file in generated_file_values))

    def test_mutant_creation_append(self):
        self.dc['a'] = ['1', ]
        self.dc['b'] = ['2', ]
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                True, self.fuzzer_config)

        expected_dc_lst = [DataContainer([('a', ['1abc']), ('b', ['2'])]),
                           DataContainer([('a', ['1def']), ('b', ['2'])]),
                           DataContainer([('a', ['1']), ('b', ['2abc'])]),
                           DataContainer([('a', ['1']), ('b', ['2def'])])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_mutant_creation_repeated_params(self):
        self.dc['a'] = ['1', '2']
        self.dc['b'] = ['3', ]
        freq = FuzzableRequest(self.url, dc=self.dc)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                False, self.fuzzer_config)

        expected_dc_lst = [DataContainer([('a', ['abc', '2']), ('b', ['3'])]),
                           DataContainer([('a', ['def', '2']), ('b', ['3'])]),
                           DataContainer([('a', ['1', 'abc']), ('b', ['3'])]),
                           DataContainer([('a', ['1', 'def']), ('b', ['3'])]),
                           DataContainer([('a', ['1', '2']), ('b', ['abc'])]),
                           DataContainer([('a', ['1', '2']), ('b', ['def'])])]

        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

        self.assertEqual(created_mutants[0].get_var(), 'a')
        self.assertEqual(created_mutants[0].get_var_index(), 0)
        self.assertEqual(created_mutants[0].get_original_value(), '1')
        self.assertEqual(created_mutants[2].get_var(), 'a')
        self.assertEqual(created_mutants[2].get_var_index(), 1)
        self.assertEqual(created_mutants[2].get_original_value(), '2')

    def test_mutant_creation_qs_and_postdata(self):
        original_form = Form()
        original_form.add_input([("name", "username"), ("value", "")])
        original_form.add_input([("name", "password"), ("value", "")])

        url = URL('http://moth/foo.bar?action=login')

        freq = HTTPPostDataRequest(url, dc=original_form)

        created_mutants = Mutant.create_mutants(freq, self.payloads, [],
                                                False, self.fuzzer_config)

        expected_dc_lst = [Form(
            [('username', ['abc']), ('password', ['FrAmE30.'])]),
            Form([('username', [
                   'def']), ('password', ['FrAmE30.'])]),
            Form([('username', [
                   'John8212']), ('password', ['abc'])]),
            Form([('username', ['John8212']), ('password', ['def'])]), ]

        created_dc_lst = [i.get_dc() for i in created_mutants]
        created_urls = [i.get_uri() for i in created_mutants]

        self.assertEqual(created_urls, [url, ] * 4)
        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_mutant_smart_fill_simple(self):
        original_form = Form()
        original_form.add_input([("name", "username"), ("value", "")])
        original_form.add_input([("name", "address"), ("value", "")])

        freq = HTTPPostDataRequest(self.url, dc=original_form)

        filled_form = mutant_smart_fill(freq, original_form, 'username',
                                        0, self.fuzzer_config)

        self.assertEqual(id(original_form), id(filled_form))
        self.assertEqual(filled_form['username'], ['', ])
        self.assertEqual(filled_form['address'], ['Bonsai Street 123', ])

    def test_mutant_smart_fill_with_file(self):
        original_form = Form()
        original_form.add_input([("name", "username"), ("value", "")])
        original_form.add_input([("name", "address"), ("value", "")])
        original_form.add_file_input([("name", "file"), ("type", "file")])

        freq = HTTPPostDataRequest(self.url, dc=original_form)

        filled_form = mutant_smart_fill(freq, original_form, 'username',
                                        0, self.fuzzer_config)

        self.assertEqual(id(original_form), id(filled_form))
        self.assertEqual(filled_form['username'], ['', ])
        self.assertEqual(filled_form['address'], ['Bonsai Street 123', ])

        str_file = filled_form['file'][0]
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertIn('GIF', str_file)
