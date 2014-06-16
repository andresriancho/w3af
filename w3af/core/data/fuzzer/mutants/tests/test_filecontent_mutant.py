"""
test_filecontent_mutant.py

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

from mock import patch

from w3af.core.data.constants.file_templates.file_templates import get_template_with_payload
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.filecontent_mutant import FileContentMutant
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.multipart import encode_as_multipart, get_boundary
from w3af.core.controllers.misc.io import NamedStringIO


class TestFileContentMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_form_files': True,
                              'fuzzed_files_extension': 'gif'}
        self.payloads = ['abc', 'def']
        self.url = URL('http://moth/')

    def test_basics(self):
        form = FormParameters()
        form.set_method('POST')
        form.set_action(self.url)
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form.add_file_input([("name", "file"), ("type", "file")])

        freq = FuzzableRequest.from_form(form)

        m = FileContentMutant(freq)
        m.get_dc().set_token('file', 0)
        m.set_token_value('abc')
        self.assertEqual(m.get_url().url_string, 'http://moth/')

        expected_mod_value = 'The data that was sent is: "username=&file=abc&address=".'
        generated_mod_value = m.print_token_value()

        self.assertEqual(generated_mod_value, expected_mod_value)

        expected_found_at = u'"http://moth/", using HTTP method POST. The'\
            u' sent post-data was: "username=&file=abc&address="'\
            u' which modified the uploaded file content.'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_config_false(self):
        fuzzer_config = {'fuzz_form_files': False}
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = FileContentMutant.create_mutants(freq,
                                                             self.payloads, [],
                                                             False,
                                                             fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_generate_all(self):
        fuzzer_config = {'fuzz_form_files': True,
                         'fuzzed_files_extension': 'gif'}

        form = FormParameters()
        form.set_method('POST')
        form.set_action(self.url)
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form.add_file_input([("name", "image"), ("type", "file")])

        freq = FuzzableRequest.from_form(form)

        ph = 'w3af.core.data.constants.file_templates.file_templates.rand_alpha'

        with patch(ph) as mock_rand_alpha:
            mock_rand_alpha.return_value = 'upload'
            generated_mutants = FileContentMutant.create_mutants(freq,
                                                                 self.payloads,
                                                                 [], False,
                                                                 fuzzer_config)

        self.assertEqual(len(generated_mutants), 2, generated_mutants)

        _, file_payload_abc, _ = get_template_with_payload('gif', 'abc')
        _, file_payload_def, _ = get_template_with_payload('gif', 'def')

        file_abc = NamedStringIO(file_payload_abc, 'upload.gif')
        file_def = NamedStringIO(file_payload_def, 'upload.gif')

        expected_forms = [Form([('username', ['John8212']),
                                ('address', ['Bonsai Street 123']),
                                ('image', [file_abc])]),
                          Form([('username', ['John8212']),
                                ('address', ['Bonsai Street 123']),
                                ('image', [file_def])])]

        boundary = get_boundary()
        noop = '1' * len(boundary)

        expected_data = [encode_as_multipart(f, boundary) for f in expected_forms]
        expected_data = set([s.replace(boundary, noop) for s in expected_data])

        generated_forms = [m.get_dc() for m in generated_mutants]
        generated_data = [str(f).replace(f.boundary, noop) for f in generated_forms]

        self.assertEqual(expected_data, set(generated_data))

        str_file = generated_forms[0]['image'][0].get_value()
        self.assertIsInstance(str_file, NamedStringIO)
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertEqual(file_payload_abc, str_file)

        str_file = generated_forms[1]['image'][0].get_value()
        self.assertIsInstance(str_file, NamedStringIO)
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertEqual(file_payload_def, str_file)

        self.assertIn('name="image"; filename="upload.gif"', generated_data[0])