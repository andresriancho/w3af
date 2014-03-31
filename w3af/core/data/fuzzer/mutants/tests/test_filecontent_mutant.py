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

from w3af.core.data.parsers.url import URL
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from w3af.core.data.fuzzer.mutants.filecontent_mutant import FileContentMutant
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.dc.form import Form


class TestFileContentMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_form_files': True,
                              'fuzzed_files_extension': 'gif'}
        self.payloads = ['abc', 'def']
        self.url = URL('http://moth/')

    def test_basics(self):
        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form.add_file_input([("name", "file"), ("type", "file")])

        freq = HTTPPostDataRequest(self.url, dc=form)

        m = FileContentMutant(freq)
        m.set_var('file', 0)
        m.set_mod_value('abc')
        self.assertEqual(m.get_url().url_string, 'http://moth/')

        expected_mod_value = 'The data that was sent is: "username=&file=abc&address=".'
        generated_mod_value = m.print_mod_value()

        self.assertEqual(generated_mod_value, expected_mod_value)

        expected_found_at = u'"http://moth/", using HTTP method POST. The'\
            ' sent post-data was: "username=&file=abc&address="'\
            ' which modifies the uploaded file content.'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_config_false(self):
        fuzzer_config = {'fuzz_form_files': False}
        freq = HTTPPostDataRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = FileContentMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_config_true(self):
        fuzzer_config = {'fuzz_form_files': True,
                         'fuzzed_files_extension': 'gif'}

        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form.add_file_input([("name", "file"), ("type", "file")])

        freq = HTTPPostDataRequest(self.url, dc=form)

        generated_mutants = FileContentMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertNotEqual(len(generated_mutants), 0, generated_mutants)

    def test_valid_results(self):
        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_file_input([("name", "file"), ("type", "file")])

        freq = HTTPPostDataRequest(self.url, dc=form)

        generated_mutants = FileContentMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 2, generated_mutants)

        expected_data = [Form([('username', ['John8212']), ('file', ['abc'])]),
                         Form([('username', ['John8212']), ('file', ['def'])]), ]

        generated_data = [m.get_data() for m in generated_mutants]

        self.assertEqual(expected_data, generated_data)

        str_file = generated_data[0]['file'][0]
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertIn('abc', str_file)
