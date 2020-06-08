"""
test_postdata_mutant.py

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
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.utils.form_params import FormParameters


class TestPostDataMutant(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {}

    def test_found_at(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])

        form = URLEncodedForm(form_params)
        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'), post_data=form,
                               method='PUT')
        m = PostDataMutant(freq)
        m.get_dc().set_token(('username', 0))

        expected = '"http://www.w3af.com/?id=3", using HTTP method PUT. '\
                   'The sent post-data was: "username=&address=" '\
                   'which modifies the "username" parameter.'
        self.assertEqual(m.found_at(), expected)

    def test_mutant_creation(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])

        form = URLEncodedForm(form_params)
        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'), post_data=form,
                               method='PUT')

        created_mutants = PostDataMutant.create_mutants(freq, self.payloads, [],
                                                        False,
                                                        self.fuzzer_config)

        expected_dcs = ['username=def&address=Bonsai%20Street%20123',
                        'username=abc&address=Bonsai%20Street%20123',
                        'username=John8212&address=def',
                        'username=John8212&address=abc']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEqual(set(created_dcs), set(expected_dcs))

        token = created_mutants[0].get_token()
        self.assertEqual(token.get_name(), 'username')
        self.assertEqual(token.get_original_value(), '')
        self.assertEqual(token.get_value(), 'abc')

        token = created_mutants[1].get_token()
        self.assertEqual(token.get_name(), 'address')
        self.assertEqual(token.get_original_value(), '')
        self.assertEqual(token.get_value(), 'abc')

        token = created_mutants[2].get_token()
        self.assertEqual(token.get_name(), 'username')
        self.assertEqual(token.get_original_value(), '')
        self.assertEqual(token.get_value(), 'def')

        token = created_mutants[3].get_token()
        self.assertEqual(token.get_name(), 'address')
        self.assertEqual(token.get_original_value(), '')
        self.assertEqual(token.get_value(), 'def')

        for m in created_mutants:
            self.assertIsInstance(m, PostDataMutant)

        for m in created_mutants:
            self.assertEqual(m.get_method(), 'PUT')

    def test_mutant_creation_repeated_parameter_name(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "id"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "id"), ("value", "")])

        form = URLEncodedForm(form_params)
        freq = FuzzableRequest(URL('http://w3af.com/?foo=3'), post_data=form,
                               method='GET')

        created_mutants = PostDataMutant.create_mutants(freq, self.payloads, [],
                                                        False,
                                                        self.fuzzer_config)

        expected_dcs = ['id=def&id=3419',
                        'id=3419&id=def',
                        'id=3419&id=abc',
                        'id=abc&id=3419']

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEqual(set(created_dcs), set(expected_dcs))

        token = created_mutants[0].get_token()
        self.assertEqual(token.get_name(), 'id')
        self.assertEqual(token.get_original_value(), '')

        token = created_mutants[2].get_token()
        self.assertEqual(token.get_name(), 'id')
        self.assertEqual(token.get_original_value(), '')

        for m in created_mutants:
            self.assertIsInstance(m, PostDataMutant)

        for m in created_mutants:
            self.assertEqual(m.get_method(), 'GET')

    def test_mutant_creation_file(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "default")])
        form_params.add_field_by_attr_items([("name", "file_upload"), ("type", "file")])

        form = MultipartContainer(form_params)
        freq = FuzzableRequest(URL('http://www.w3af.com/upload'),
                               post_data=form, method='POST')

        payloads = [file(__file__)]
        created_mutants = PostDataMutant.create_mutants(freq, payloads,
                                                        ['file_upload', ],
                                                        False,
                                                        self.fuzzer_config)

        self.assertEqual(len(created_mutants), 1, created_mutants)
        
        mutant = created_mutants[0]
        
        self.assertIsInstance(mutant.get_token().get_value(), file)
        self.assertEqual(mutant.get_dc()['username'][0], 'default')

