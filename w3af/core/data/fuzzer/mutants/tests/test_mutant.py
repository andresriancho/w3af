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
import urllib

from w3af.core.data.constants.file_templates.file_templates import get_file_from_template
from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.multipart_container import MultipartContainer


class FakeMutant(Mutant):
    """
    In order to test the Mutant base class methods, I had to create this "fake"
    mutant, which helps with the implementation of required methods.
    """
    def get_dc(self):
        return self.get_fuzzable_req().get_uri().querystring

    def set_dc(self, new_qs):
        self.get_fuzzable_req().get_uri().querystring = new_qs


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
                        'a=def&b=2', 'a=1&b=def',]

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
                        'a=def&b=2', 'a=1&b=def',]

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
        self.assertEqual(mutant.print_token_value(),
                         'The data that was sent is: "".')
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
        form_params.add_input([("name", "username"), ("value", "")])
        form_params.add_input([("name", "address"), ("value", "")])
        form_params.add_file_input([("name", "file"), ("type", "file")])

        form = MultipartContainer(form_params)
        freq = FuzzableRequest(self.url, post_data=form)

        created_mutants = PostDataMutant.create_mutants(freq, self.payloads, [],
                                                        False,
                                                        self.fuzzer_config)
        _abc = self.payloads[0]
        _def = self.payloads[1]
        name = 'John8212'
        address = urllib.quote('Bonsai Street 123')

        _, gif_file, _ = get_file_from_template('gif')
        gif_file = urllib.quote(gif_file)

        fmt = 'username=%s&file=%s&address=%s'

        # TODO: There are some useless mutants being generated here, which send
        # "abc" and "def" as the file content: and don't even use a
        # NamedStringIO to do it -so it will be sent as a common var not a file-
        # and on top of that, it doesn't even look like a file content.
        #
        # The good thing is that this will only happen for forms with files
        # (not so common) and it might even trigger a traceback ;)
        expected_dcs = [
                        fmt % (_abc, gif_file, address),
                        fmt % (name, gif_file, _abc),
                        fmt % (name, _abc, address), # useless
                        fmt % (_def, gif_file, address),
                        fmt % (name, gif_file, _def),
                        fmt % (name, _def, address), # useless
                        ]

        created_dcs = [str(i.get_dc()) for i in created_mutants]

        self.assertEquals(expected_dcs, created_dcs)

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
        form_params.add_input([("name", "username"), ("value", "")])
        form_params.add_input([("name", "password"), ("value", "")])

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

