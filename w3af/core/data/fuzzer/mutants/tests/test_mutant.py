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
import copy

from mock import patch

from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.constants.file_templates.file_templates import get_file_from_template
from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.data.dc.utils.multipart import encode_as_multipart, get_boundary


class FakeMutant(Mutant):
    """
    In order to test the Mutant base class methods, I had to create this "fake"
    mutant, which helps with the implementation of required methods.
    """
    def get_dc(self):
        return self.get_fuzzable_request().get_uri().querystring

    def set_dc(self, new_qs):
        self.get_fuzzable_request().get_uri().querystring = new_qs


class TestMutant(unittest.TestCase):

    SIMPLE_KV = [('a', ['1']), ('b', ['2'])]

    def setUp(self):
        self.url = URL('http://moth/')
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {'fuzz_form_files': 'gif'}

    def test_required_methods(self):
        m = Mutant(FuzzableRequest(self.url))
        self.assertRaises(NotImplementedError, m.get_dc)
        self.assertRaises(NotImplementedError, m.set_dc, None)

    def test_mutant_creation(self):
        qs = QueryString(self.SIMPLE_KV)
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
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

        self.assertTrue(all(isinstance(m, Mutant) for m in created_mutants))
        self.assertTrue(all(m.get_mutant_class() == 'FakeMutant' for m in created_mutants))

    def test_alternative_mutant_creation(self):
        freq = FuzzableRequest(URL('http://moth/?a=1&b=2'))

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        expected_dcs = ['a=abc&b=2', 'a=1&b=abc',
                        'a=def&b=2', 'a=1&b=def']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

    def test_get_mutant_class(self):
        m = Mutant(None)
        self.assertEqual(m.get_mutant_class(), 'Mutant')

    def test_mutant_generic_methods(self):
        qs = QueryString(self.SIMPLE_KV)
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        mutant = created_mutants[0]

        self.assertEqual(repr(mutant),
                         '<mutant-generic | GET | http://moth/?a=abc&b=2 >')
        self.assertNotEqual(id(mutant.copy()), id(mutant))

        self.assertRaises(ValueError, mutant.get_original_response_body)

        body = 'abcdef123'
        mutant.set_original_response_body(body)
        self.assertEqual(mutant.get_original_response_body(), body)

    def test_mutant_creation_ignore_params(self):
        qs = QueryString(self.SIMPLE_KV)
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, ['a'],
                                                    False, self.fuzzer_config)

        expected_dcs = ['a=abc&b=2', 'a=def&b=2']
        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEqual(expected_dcs, created_dcs)

    def test_mutant_creation_empty_dc(self):
        qs = QueryString()
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        expected_dc_lst = []
        created_dc_lst = [i.get_dc() for i in created_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_mutant_creation_post_data(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "image"), ("type", "file")])

        form = MultipartContainer(form_params)
        freq = FuzzableRequest(self.url, post_data=form)

        ph = 'w3af.core.data.constants.file_templates.file_templates.rand_alpha'

        with patch(ph) as mock_rand_alpha:
            mock_rand_alpha.return_value = 'upload'
            generated_mutants = PostDataMutant.create_mutants(freq,
                                                              self.payloads, [],
                                                              False,
                                                              self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 6, generated_mutants)

        _, gif_file_content, _ = get_file_from_template('gif')
        gif_named_stringio = NamedStringIO(gif_file_content, 'upload.gif')

        expected_forms = []

        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = [gif_named_stringio]
        form['username'] = ['def']
        form['address'] = ['Bonsai Street 123']
        expected_forms.append(form)

        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = [gif_named_stringio]
        form['username'] = ['abc']
        form['address'] = ['Bonsai Street 123']
        expected_forms.append(form)

        # TODO: Please note that these two multipart forms are a bug, since
        #       they should never be created by PostDataMutant.create_mutants
        #       (they are not setting the image as a file, just as a string)
        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = ['def']
        form['username'] = ['John8212']
        form['address'] = ['Bonsai Street 123']
        expected_forms.append(form)

        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = ['abc']
        form['username'] = ['John8212']
        form['address'] = ['Bonsai Street 123']
        expected_forms.append(form)
        #
        # TODO: /end
        #

        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = [gif_named_stringio]
        form['username'] = ['John8212']
        form['address'] = ['abc']
        expected_forms.append(form)

        form = MultipartContainer(copy.deepcopy(form_params))
        form['image'] = [gif_named_stringio]
        form['username'] = ['John8212']
        form['address'] = ['def']
        expected_forms.append(form)

        boundary = get_boundary()
        noop = '1' * len(boundary)

        expected_data = [encode_as_multipart(f, boundary) for f in expected_forms]
        expected_data = set([s.replace(boundary, noop) for s in expected_data])

        generated_forms = [m.get_dc() for m in generated_mutants]
        generated_data = [str(f).replace(f.boundary, noop) for f in generated_forms]

        self.assertEqual(expected_data, set(generated_data))

        str_file = generated_forms[0]['image'][0]
        self.assertIsInstance(str_file, NamedStringIO)
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertEqual(gif_file_content, str_file)

        str_file = generated_forms[1]['image'][0]
        self.assertIsInstance(str_file, NamedStringIO)
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertEqual(gif_file_content, str_file)

        self.assertIn('name="image"; filename="upload.gif"', generated_data[0])

    def test_mutant_creation_append(self):
        qs = QueryString(self.SIMPLE_KV)
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
                                                    True, self.fuzzer_config)

        expected_dcs = ['a=1abc&b=2', 'a=1&b=2abc',
                        'a=1def&b=2', 'a=1&b=2def',]

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

    def test_mutant_creation_repeated_params(self):
        qs = QueryString([('a', ['1', '2']), ('b', ['3'])])
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        created_mutants = FakeMutant.create_mutants(freq, self.payloads, [],
                                                    False, self.fuzzer_config)

        expected_dcs = ['a=abc&a=2&b=3',
                        'a=1&a=abc&b=3',
                        'a=1&a=2&b=abc',
                        'a=def&a=2&b=3',
                        'a=1&a=def&b=3',
                        'a=1&a=2&b=def']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

        token_0 = created_mutants[0].get_token()
        self.assertIsInstance(token_0, DataToken)
        self.assertEqual(token_0.get_name(), 'a')
        self.assertEqual(token_0.get_original_value(), '1')
        self.assertEqual(token_0.get_value(), 'abc')

        token_1 = created_mutants[1].get_token()
        self.assertIsInstance(token_1, DataToken)
        self.assertEqual(token_1.get_name(), 'a')
        self.assertEqual(token_1.get_original_value(), '2')
        self.assertEqual(token_1.get_value(), 'abc')

    def test_mutant_creation_qs_and_postdata(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "password"), ("value", "")])

        url = URL('http://moth/foo.bar?action=login')

        form = URLEncodedForm(form_params)
        freq = FuzzableRequest(url, post_data=form)

        created_mutants = PostDataMutant.create_mutants(freq, self.payloads, [],
                                                        False,
                                                        self.fuzzer_config)
        created_dcs = [str(i.get_dc()) for i in created_mutants]

        expected_dcs = ['username=abc&password=FrAmE30.',
                        'username=John8212&password=abc',
                        'username=def&password=FrAmE30.',
                        'username=John8212&password=def']

        self.assertEqual(created_dcs, expected_dcs)

        for m in created_mutants:
            self.assertEqual(m.get_uri(), url)

    def test_mutant_copy(self):
        qs = QueryString(self.SIMPLE_KV)
        freq = FuzzableRequest(self.url)
        freq.set_querystring(qs)

        mutant = FakeMutant(freq)
        mutant.set_token(('a', 0))

        mutant_copy = mutant.copy()

        self.assertEqual(mutant, mutant_copy)
        self.assertEqual(mutant.get_token(), mutant_copy.get_token())
        self.assertIsNot(None, mutant_copy.get_token())
