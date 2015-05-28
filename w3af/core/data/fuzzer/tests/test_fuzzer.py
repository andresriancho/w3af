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
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.cookie_mutant import CookieMutant
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.fuzzer.mutants.filename_mutant import FileNameMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.fuzzer.mutants.xmlrpc_mutant import XmlRpcMutant
from w3af.core.data.parsers.doc.tests.test_xmlrpc import XML_WITH_FUZZABLE
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.urlencoded_form import URLEncodedForm


class TestFuzzer(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.cf_backup = Config(cf_singleton)

    def tearDown(self):
        cf_singleton = self.cf_backup

    def assertAllInstance(self, items, _type):
        for item in items:
            self.assertIsInstance(item, _type)

    def assertAllHaveTokens(self, items):
        self.assertTrue(all([m.get_token() is not None for m in items]))

    def test_simple(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(generated_mutants, QSMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_empty_string_as_payload(self):
        url = URL('http://moth/?id=1&spam=2')
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, [''])

        expected_urls = ['http://moth/?id=&spam=2',
                         'http://moth/?id=1&spam=']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(generated_mutants, QSMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_empty_string_as_payload_one_param(self):
        url = URL('http://moth/?id=1')
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, [''])

        expected_urls = ['http://moth/?id=']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(generated_mutants, QSMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_special_url_characters(self):
        initial_url = 'http://w3af.org/' \
                      '?__VIEWSTATE=/' \
                      '&__EVENTVALIDATION=\\X+W=='\
                      '&_ctl0:TextBox1=%s'

        url = URL(initial_url % '')
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        decoded_url = 'http://w3af.org/' \
                      '?__VIEWSTATE=/' \
                      '&__EVENTVALIDATION=\\X%%20W=='\
                      '&_ctl0:TextBox1=%s'

        expected_urls = [decoded_url % 'abc',
                         decoded_url % 'def']
        generated_urls = [str(m.get_uri()) for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(generated_mutants, QSMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_fuzz_headers_no_headers_in_request(self):
        cf_singleton.save('fuzzable_headers', ['Referer'])  # This one changed
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # No headers in the original request
        #headers = Headers([('Referer', 'http://moths/')])
        freq = FuzzableRequest(url)
        mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def',
                         'http://moth/?id=1',
                         'http://moth/?id=1', ]
        generated_urls = [m.get_uri().url_string for m in mutants]

        self.assertEqual(generated_urls, expected_urls)

        expected_headers = [Headers([('Referer', '')]),
                            Headers([('Referer', '')]),
                            Headers([('Referer', 'abc')]),
                            Headers([('Referer', 'def')]), ]

        generated_headers = [m.get_headers() for m in mutants]

        self.assertEqual(expected_headers, generated_headers)
        self.assertAllInstance(mutants[:2], QSMutant)
        self.assertAllInstance(mutants[2:], HeadersMutant)
        self.assertAllHaveTokens(mutants)

    def test_fuzz_headers(self):
        cf_singleton.save('fuzzable_headers', ['Referer'])  # This one changed
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # With headers
        headers = Headers([('Referer', 'http://moths/'),
                           ('Foo', 'Bar')])
        freq = FuzzableRequest(url, headers=headers)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def',
                         'http://moth/?id=1',
                         'http://moth/?id=1', ]
        generated_urls = [m.get_uri().url_string for m in generated_mutants]
        self.assertEqual(generated_urls, expected_urls)

        expected_headers = [
            headers,
            headers,
            Headers([('Referer', 'abc'), ('Foo', 'Bar')]),
            Headers([('Referer', 'def'), ('Foo', 'Bar')]),]

        generated_headers = [m.get_headers() for m in generated_mutants]
        self.assertEqual(expected_headers, generated_headers)

        self.assertAllInstance(generated_mutants[:2], QSMutant)
        self.assertAllInstance(generated_mutants[2:], HeadersMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_no_cookie_in_request(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', True)  # This one changed
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # But there is no cookie
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        expected_urls = ['http://moth/?id=abc',
                         'http://moth/?id=def']
        generated_urls = [m.get_uri().url_string for m in generated_mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(generated_mutants, QSMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_qs_and_cookie(self):
        """
        Even when fuzz_cookies is True, we won't create HeaderMutants based
        on a FuzzableRequest. This is one of the ugly things related with

            https://github.com/andresriancho/w3af/issues/3149

        Which we fixed!
        """
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', True)  # This one changed
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/?id=1')
        # And now there is a cookie
        cookie = Cookie('foo=bar')
        freq = FuzzableRequest(url, cookie=cookie)
        mutants = create_mutants(freq, self.payloads)

        expected_urls = [u'http://moth/?id=abc',
                         u'http://moth/?id=def',
                         u'http://moth/?id=1',
                         u'http://moth/?id=1']

        generated_urls = [m.get_uri().url_string for m in mutants]

        self.assertEqual(generated_urls, expected_urls)
        self.assertAllInstance(mutants[:2], QSMutant)
        self.assertAllInstance(mutants[2:], CookieMutant)
        self.assertAllHaveTokens(mutants)

    def test_filename_only_dir_path(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', True)  # This one changed
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/')
        freq = FuzzableRequest(url)
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
        freq = FuzzableRequest(url)
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

        self.assertAllInstance(generated_mutants[:2], QSMutant)
        self.assertAllInstance(generated_mutants[2:], FileNameMutant)
        self.assertAllHaveTokens(generated_mutants)

    def test_form_file_qs(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', True)  # This one changed
        cf_singleton.save('fuzz_url_parts', False)

        url = URL('http://moth/foo.htm')
        freq = FuzzableRequest(url)
        generated_mutants = create_mutants(freq, self.payloads)

        self.assertEqual(generated_mutants, [])

    def test_xmlrpc_mutant(self):
        url = URL('http://moth/?id=1')
        post_data = XML_WITH_FUZZABLE
        headers = Headers()
        freq = FuzzableRequest.from_parts(url, 'POST', post_data, headers)
        mutants = create_mutants(freq, self.payloads)

        self.assertAllInstance(mutants[:2], QSMutant)
        self.assertAllInstance(mutants[4:], XmlRpcMutant)
        self.assertAllHaveTokens(mutants)

    def test_form_file_post_no_files(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', True)  # This one changed
        cf_singleton.save('fuzz_url_parts', False)

        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("value", "")])
        form_params.add_field_by_attr_items([("name", "address"), ("value", "")])

        form = URLEncodedForm(form_params)

        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'), post_data=form,
                               method='PUT')

        mutants = create_mutants(freq, self.payloads)

        self.assertTrue(all(isinstance(m, QSMutant) for m in mutants[:2]))
        self.assertTrue(all(isinstance(m, PostDataMutant) for m in mutants[4:]))

        self.assertTrue(all(m.get_method() == 'PUT' for m in mutants))

        expected_uris = {'http://www.w3af.com/?id=abc',
                         'http://www.w3af.com/?id=def',
                         'http://www.w3af.com/?id=3',
                         'http://www.w3af.com/?id=3',
                         'http://www.w3af.com/?id=3',
                         'http://www.w3af.com/?id=3'}
        created_uris = set([i.get_uri().url_string for i in mutants])
        self.assertEqual(expected_uris, created_uris)

        expected_dcs = {'id=abc', 'id=def',
                        'username=abc&address=Bonsai%20Street%20123',
                        'username=def&address=Bonsai%20Street%20123',
                        'username=John8212&address=abc',
                        'username=John8212&address=def'}

        created_dcs = set([str(i.get_dc()) for i in mutants])
        self.assertEqual(created_dcs, expected_dcs)

    def test_urlparts_no_path(self):
        cf_singleton.save('fuzzable_headers', [])
        cf_singleton.save('fuzz_cookies', False)
        cf_singleton.save('fuzz_url_filenames', False)
        cf_singleton.save('fuzzed_files_extension', 'gif')
        cf_singleton.save('fuzz_form_files', False)
        cf_singleton.save('fuzz_url_parts', True)  # This one changed

        url = URL('http://moth/')
        freq = FuzzableRequest(url)
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
        freq = FuzzableRequest(url)
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
