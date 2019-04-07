"""
test_urlparts_mutant.py

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
import cPickle

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.urlparts_mutant import (URLPartsMutant,
                                                           TOKEN,
                                                           URLPartsContainer)


class TestURLPartsMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_url_parts': True}
        self.payloads = ['abc', 'def']

    def test_basics(self):
        divided_path = URLPartsContainer('/', 'ping!', '/bar')

        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))
        m = URLPartsMutant(freq)
        m.set_dc(divided_path)
        self.assertEqual(m.get_url().url_string,
                         u'http://www.w3af.com/ping%21/bar')

        expected_found_at = '"http://www.w3af.com/ping%21/bar", using HTTP method'\
                            ' GET. The modified parameter was the URL path, with'\
                            ' value: "ping!".'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_pickle(self):
        divided_path = URLPartsContainer('/', 'ping!', '/bar')
        loaded_dp = cPickle.loads(cPickle.dumps(divided_path))

        self.assertEqual(loaded_dp, divided_path)
        self.assertEqual(loaded_dp.url_start, divided_path.url_start)
        self.assertEqual(loaded_dp.url_end, divided_path.url_end)
        self.assertEqual(loaded_dp[TOKEN], divided_path[TOKEN])

    def test_config_false(self):
        fuzzer_config = {'fuzz_url_parts': False}
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = URLPartsMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_config_true(self):
        fuzzer_config = {'fuzz_url_parts': True}
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = URLPartsMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertNotEqual(len(generated_mutants), 0, generated_mutants)

    def test_valid_results(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = URLPartsMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 4, generated_mutants)

        expected_urls = [URL('http://www.w3af.com/abc/bar'),
                         URL('http://www.w3af.com/def/bar'),
                         URL('http://www.w3af.com/foo/abc'),
                         URL('http://www.w3af.com/foo/def')]

        generated_urls = [m.get_url() for m in generated_mutants]

        self.assertEqual(expected_urls, generated_urls)

    def test_valid_results_double_encoding(self):
        """
        In this case the number of generated mutants is higher due to the
        encoded and double encoded versions which are returned. In the previous
        case, and given that both the encoded and double encoded versions were
        the same, the number of generated mutants was 4.
        """
        payloads = ['ls - la', 'ping 127.0.0.1 -c 5',
                    'http://127.0.0.1:8015/test/']
        freq = FuzzableRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = URLPartsMutant.create_mutants(freq, payloads, [],
                                                          False,
                                                          self.fuzzer_config)

        expected_urls = ['http://www.w3af.com/ls+-+la/bar',
                         'http://www.w3af.com/ls%2B-%2Bla/bar',
                         'http://www.w3af.com/ping+127.0.0.1+-c+5/bar',
                         'http://www.w3af.com/ping%2B127.0.0.1%2B-c%2B5/bar',
                         'http://www.w3af.com/foo/ls+-+la',
                         'http://www.w3af.com/foo/ls%2B-%2Bla',
                         'http://www.w3af.com/foo/ping+127.0.0.1+-c+5',
                         'http://www.w3af.com/foo/ping%2B127.0.0.1%2B-c%2B5',
                         'http://www.w3af.com/http%3A%2F%2F127.0.0.1%3A8015%2Ftest%2F/bar',
                         'http://www.w3af.com/http%253A%252F%252F127.0.0.1%253A8015%252Ftest%252F/bar',
                         'http://www.w3af.com/foo/http%3A%2F%2F127.0.0.1%3A8015%2Ftest%2F',
                         'http://www.w3af.com/foo/http%253A%252F%252F127.0.0.1%253A8015%252Ftest%252F']

        generated_urls = set([m.get_url().url_string for m in generated_mutants])

        self.assertEqual(set(expected_urls), generated_urls)

    def test_forced_url_parts(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/static/foo/bar.ext'))
        freq.set_force_fuzzing_url_parts([
            ('/static/', False),
            ('foo', True),
            ('/bar.', False),
            ('ext', True)
        ])

        generated_mutants = URLPartsMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        expected_urls = ['http://www.w3af.com/static/abc/bar.ext',
                         'http://www.w3af.com/static/def/bar.ext',
                         'http://www.w3af.com/static/foo/bar.abc',
                         'http://www.w3af.com/static/foo/bar.def']

        generated_urls = set([m.get_url().url_string for m in generated_mutants])

        self.assertEqual(set(expected_urls), generated_urls)

    def test_forced_url_parts_qs(self):
        freq = FuzzableRequest(URL('http://www.w3af.com/static/foo/bar.ext?foo=bar'))
        freq.set_force_fuzzing_url_parts([
            ('/static/', False),
            ('foo', True),
            ('/bar.', False),
            ('ext', True)
        ])

        generated_mutants = URLPartsMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        expected_uris = ['http://www.w3af.com/static/abc/bar.ext?foo=bar',
                         'http://www.w3af.com/static/def/bar.ext?foo=bar',
                         'http://www.w3af.com/static/foo/bar.abc?foo=bar',
                         'http://www.w3af.com/static/foo/bar.def?foo=bar']

        generated_uris = set([m.get_uri().url_string for m in generated_mutants])

        self.assertEqual(set(expected_uris), generated_uris)
