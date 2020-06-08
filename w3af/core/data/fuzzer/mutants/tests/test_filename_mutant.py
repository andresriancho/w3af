"""
test_filename_mutant.py

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
from w3af.core.data.fuzzer.mutants.filename_mutant import FileNameMutant
from w3af.core.data.fuzzer.mutants.urlparts_mutant import URLPartsContainer


class TestFileNameMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_url_filenames': True}
        self.payloads = ['abc', 'def']

    def test_basics(self):
        parts = URLPartsContainer('', 'ping!', '.htm')

        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar.htm'))
        m = FileNameMutant(freq)
        m.set_dc(parts)

        self.assertEqual(m.get_url().url_string,
                         u'http://www.w3af.com/foo/ping%21.htm')

        expected_found_at = '"http://www.w3af.com/foo/ping%21.htm", using HTTP'\
                            ' method GET. The modified parameter was the URL'\
                            ' filename, with value: "ping!".'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_config_false(self):
        fuzzer_config = {'fuzz_url_filenames': False}
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = FileNameMutant.create_mutants(freq, self.payloads,
                                                          [], False,
                                                          fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_config_true(self):
        fuzzer_config = {'fuzz_url_filenames': True}
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = FileNameMutant.create_mutants(freq, self.payloads,
                                                          [], False,
                                                          fuzzer_config)

        self.assertNotEqual(len(generated_mutants), 0, generated_mutants)

    def test_valid_results(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar.htm'))

        generated_mutants = FileNameMutant.create_mutants(freq, self.payloads,
                                                          [], False,
                                                          self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 4, generated_mutants)

        expected_urls = [URL('http://www.w3af.com/foo/abc.htm'),
                         URL('http://www.w3af.com/foo/def.htm'),
                         URL('http://www.w3af.com/foo/bar.abc'),
                         URL('http://www.w3af.com/foo/bar.def')]

        generated_urls = [m.get_url() for m in generated_mutants]

        self.assertEqual(expected_urls, generated_urls)

    def test_valid_results_double_encoding(self):
        """
        In this case the number of generated mutants is higher due to the
        encoded and double encoded versions which are returned. In the previous
        case, and given that both the encoded and double encoded versions were
        the same, the number of generated mutants was 4.
        """
        payloads = ['ls - la', 'http://127.0.0.1:8015/test/']
        freq = FuzzableRequest(URL('http://www.w3af.com/bar.htm'))

        generated_mutants = FileNameMutant.create_mutants(freq, payloads, [],
                                                          False,
                                                          self.fuzzer_config)

        expected_urls = ['http://www.w3af.com/ls+-+la.htm',
                         'http://www.w3af.com/bar.ls+-+la',
                         'http://www.w3af.com/http%3A%2F%2F127.0.0.1%3A8015%2Ftest%2F.htm',
                         'http://www.w3af.com/http%3A//127.0.0.1%3A8015/test/.htm',
                         'http://www.w3af.com/bar.http%3A%2F%2F127.0.0.1%3A8015%2Ftest%2F',
                         'http://www.w3af.com/bar.http%3A//127.0.0.1%3A8015/test/']

        generated_urls = [m.get_url().url_string for m in generated_mutants]
        
        self.assertEqual(set(expected_urls), set(generated_urls))
