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
import copy

from mock import patch

from w3af.core.data.constants.file_templates.file_templates import get_template_with_payload
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.filecontent_mutant import (FileContentMutant,
                                                              OnlyTokenFilesMultipartContainer)
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.multipart import encode_as_multipart, get_boundary
from w3af.core.controllers.misc.io import NamedStringIO


class TestFileContentMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_form_files': True,
                              'fuzzed_files_extension': 'gif'}
        self.payloads = ['abc', 'def']
        self.url = URL('http://moth/')

    def create_simple_filecontent_mutant(self, container_klass):
        form_params = FormParameters()
        form_params.set_method('POST')
        form_params.set_action(self.url)
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "file"), ("type", "file")])

        form = container_klass(form_params)
        freq = FuzzableRequest.from_form(form)

        m = FileContentMutant(freq)
        m.get_dc().set_token(('file', 0))
        m.set_token_value('abc')

        return m

    def test_basics(self):
        m = self.create_simple_filecontent_mutant(MultipartContainer)
        self.assertEqual(m.get_url().url_string, 'http://moth/')

        expected_found_at = u'"http://moth/", using HTTP method POST. The'\
            u' sent post-data was: "...file=abc..."'\
            u' which modified the uploaded file content.'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_copy_filecontent_mutant(self):
        m = self.create_simple_filecontent_mutant(MultipartContainer)

        mcopy = m.copy()

        self.assertEqual(m.get_token(), mcopy.get_token())
        self.assertIsNot(m.get_token(), None)

        ofr = m.get_fuzzable_request()
        cfr = mcopy.get_fuzzable_request()

        # Compare the fuzzable requests this way because the boundary "breaks"
        # the regular comparison
        self.assertEqual(ofr.get_method(), cfr.get_method())
        self.assertEqual(ofr.get_uri(), cfr.get_uri())
        self.assertEqual(ofr.get_raw_data(), cfr.get_raw_data())
        self.assertEqual(ofr.get_headers().keys(), cfr.get_headers().keys())

        # Not doing this because of the previous comment
        #self.assertEqual(ofr, cfr)
        #self.assertEqual(m, mcopy)

    def test_copy_filecontent_mutant_only_file_token(self):
        """
        Most tests are actually performed in test_copy_filecontent_mutant, but
        I want to make sure I can copy with OnlyTokenFilesMultipartContainer too
        """
        m = self.create_simple_filecontent_mutant(OnlyTokenFilesMultipartContainer)

        mcopy = m.copy()
        self.assertIsInstance(mcopy, FileContentMutant)

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

        form_params = FormParameters()
        form_params.set_method('POST')
        form_params.set_action(self.url)
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "image"), ("type", "file")])

        form = MultipartContainer(form_params)
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

        form_1 = MultipartContainer(copy.deepcopy(form_params))
        form_2 = MultipartContainer(copy.deepcopy(form_params))

        form_1['image'] = [file_abc]
        form_1['username'] = ['John8212']
        form_1['address'] = ['Bonsai Street 123']

        form_2['image'] = [file_def]
        form_2['username'] = ['John8212']
        form_2['address'] = ['Bonsai Street 123']

        expected_forms = [form_1, form_2]

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