"""
test_fuzzer.py

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

from w3af.core.data.kb.config import Config
from w3af.core.data.kb.config import cf as cf_singleton

from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.request.HTTPQsRequest import HTTPQSRequest
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from w3af.core.data.parsers.url import URL

from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.cookie_mutant import CookieMutant
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.fuzzer.mutants.filename_mutant import FileNameMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant

from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.form import Form


class TestFuzzer(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.cf_backup = Config(cf_singleton)

    def tearDown(self):
        cf_singleton = self.cf_backup

    def test_simple(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertTrue(
            all(isinstance(m, QSMutant) for m in generated_mutants))

    def test_fuzz_headers_no_headers(self):
        cf_singleton.save('fuzzable_headers', ['Referer'])  # This one changed
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # No headers in the original request
        #headers = Headers([('Referer', 'http://moth/foo/bar/')])
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def',
                         'http://moth/?id=1',
                         'http://moth/?id=1', ]
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)

        expected_headers = [Headers(),
                            Headers(),
                            Headers([('Referer', 'abc')]),
                            Headers([('Referer', 'def')]), ]

        generated_headers = [m.get_headers() for m in generated_mutants]

        self.assertEqual(expected_headers, generated_headers)

        self.assertTrue(all(isinstance(m, QSMutant) or isinstance(m, HeadersMutant)
                            for m in generated_mutants))

    def test_fuzz_headers(self):
        cf_singleton.save('fuzzable_headers', ['Referer'])  # This one changed
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # With headers
        headers = Headers([('Referer', 'http://moth/foo/bar/'),
                           ('Foo', 'Bar')])
        freq = HTTPQSRequest(url, headers=headers)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def',
                         'http://moth/?id=1',
                         'http://moth/?id=1', ]
        generated_urls = [m.get_uri().url_string for m in generated_mutants]
        self.assertEqual(generated_urls, expected_urls)

        expected_headers = [Headers(
            [('Referer', 'http://moth/foo/bar/'), ('Foo', 'Bar')]),
            Headers([('Referer',
                      'http://moth/foo/bar/'), ('Foo', 'Bar')]),
            Headers([('Referer', 'abc'), ('Foo', 'Bar')]),
            Headers([('Referer', 'def'), ('Foo', 'Bar')]), ]
        generated_headers = [m.get_headers() for m in generated_mutants]
        self.assertEqual(expected_headers, generated_headers)

        self.assertTrue(all(isinstance(m, QSMutant) or isinstance(m, HeadersMutant)
                            for m in generated_mutants))

    def test_qs_and_no_cookie(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', True)  # This one changed
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # But there is no cookie
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        #self.assertTrue( all(isinstance(m, QSMutant) for m in generated_mutants) )

    def test_qs_and_cookie(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', True)  # This one changed
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # And now there is a cookie
        cookie = Cookie('foo=bar')
        freq = HTTPQSRequest(url, cookie=cookie)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = [u'http://moth/?id=abc',
                         u'http://moth/?id=def',
                         u'http://moth/?id=1',
                         u'http://moth/?id=1']

        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)

        expected_cookies = ['foo=bar;',
                            'foo=bar;',
                            'foo=abc;',
                            'foo=def;']

        generated_cookies = [str(m.get_cookie()) for m in generated_mutants]

        self.assertEqual(expected_cookies, generated_cookies)

        self.assertTrue(all(isinstance(m, QSMutant) or isinstance(m, CookieMutant)
                            for m in generated_mutants))

    def test_filename_only_dir_path(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', True)  # This one changed
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        self.assertEqual(generated_mutants, [])

    def test_filename_fname_qs(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', True)  # This one changed
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/foo.htm?id=1')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = [u'http://moth/foo.htm?id=abc',
                         u'http://moth/foo.htm?id=def',
                         u'http://moth/abc.htm',
                         u'http://moth/def.htm',
                         u'http://moth/foo.abc',
                         u'http://moth/foo.def',
                         ]

        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)

        self.assertTrue(all(isinstance(m, QSMutant) or isinstance(m, FileNameMutant)
                            for m in generated_mutants))

    def test_form_file_qs(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', True)  # This one changed
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/foo.htm')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        self.assertEqual(generated_mutants, [])

    def test_form_file_post_no_files(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', True)  # This one changed
        cf_singleton.save('fuzz_url_parts', False)

        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])

        freq = HTTPPostDataRequest(URL('http://www.w3af.com/?id=3'), dc=form,
                                   method='PUT')

        generated_mutants = create_mutants(freq, self.payloads)

        self.assertTrue(all('http://www.w3af.com/?id=3' == m.get_uri().url_string
                            for m in generated_mutants))

        self.assertTrue(all(isinstance(m, PostDataMutant)
                            for m in generated_mutants), generated_mutants)

        self.assertTrue(
            all(m.get_method() == 'PUT' for m in generated_mutants))

        expected_dc_lst = [Form(
            [('username', ['abc']), ('address', ['Bonsai Street 123'])]),
            Form([('username', [
                   'def']), ('address', ['Bonsai Street 123'])]),
            Form([('username', [
                   'John8212']), ('address', ['abc'])]),
            Form([('username', ['John8212']), ('address', ['def'])])]

        created_dc_lst = [i.get_dc() for i in generated_mutants]

        self.assertEqual(created_dc_lst, expected_dc_lst)

    def test_urlparts_no_path(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', True)  # This one changed

        url = URL('http://moth/')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        self.assertEqual(generated_mutants, [])

    def test_urlparts_filename_path_qs(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', True)  # This one changed
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', True)  # This one changed

        url = URL('http://moth/foo/bar.htm?id=1')
        freq = HTTPQSRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        generated_uris = [m.get_uri().url_string for m in generated_mutants]
        expected_uris = [
            'http://moth/foo/bar.htm?id=abc',
            'http://moth/foo/bar.htm?id=def',
            'http://moth/foo/abc.htm',
            'http://moth/foo/def.htm',
            'http://moth/foo/bar.abc',
            'http://moth/foo/bar.def',
            'http://moth/abc/bar.htm',
            'http://moth/def/bar.htm',
            'http://moth/foo/abc',
            'http://moth/foo/def',
        ]
        self.assertEqual(generated_uris, expected_uris)
