"""
test_baseparser.py

Copyright 2012 Andres Riancho

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
from w3af.core.data.parsers.baseparser import BaseParser
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse as HTTPResponse


class TestBaseParser(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')
        response = HTTPResponse(200, '', Headers(), self.url, self.url)
        self.bp_inst = BaseParser(response)

    def test_parse_blank(self):
        response = HTTPResponse(200, '', Headers(), self.url, self.url)
        bp_inst = BaseParser(response)

        self.assertEqual(bp_inst.get_emails(), set())

        self.assertRaises(NotImplementedError, bp_inst.get_comments)
        self.assertRaises(NotImplementedError, bp_inst.get_forms)
        self.assertRaises(NotImplementedError, bp_inst.get_meta_redir)
        self.assertRaises(NotImplementedError, bp_inst.get_meta_tags)
        self.assertRaises(NotImplementedError, bp_inst.get_references)
        self.assertRaises(NotImplementedError, bp_inst.get_scripts)

    def test_get_emails_filter(self):
        response = HTTPResponse(200, '', Headers(), self.url, self.url)
        bp_inst = BaseParser(response)
        bp_inst._emails = ['a@w3af.com', 'foo@not-w3af.com']

        self.assertEqual(
            bp_inst.get_emails(), ['a@w3af.com', 'foo@not-w3af.com'])

        self.assertEqual(bp_inst.get_emails(domain='w3af.com'), ['a@w3af.com'])
        self.assertEqual(
            bp_inst.get_emails(domain='not-w3af.com'), ['foo@not-w3af.com'])

    def test_extract_emails_blank(self):
        self.assertEqual(self.bp_inst._extract_emails(''), set())

    def test_extract_emails_simple(self):
        input_str = u' abc@w3af.com '
        expected_res = set([u'abc@w3af.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_extract_emails_mailto(self):
        input_str = u'<a href="mailto:abc@w3af.com">test</a>'
        expected_res = set([u'abc@w3af.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_extract_emails_mailto_dup(self):
        input_str = u'<a href="mailto:abc@w3af.com">abc@w3af.com</a>'
        expected_res = set([u'abc@w3af.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_extract_emails_mailto_not_dup(self):
        input_str = u'<a href="mailto:abc@w3af.com">abc_def@w3af.com</a>'
        expected_res = set([u'abc@w3af.com', u'abc_def@w3af.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_extract_emails_dash(self):
        input_str = u'header abc@w3af-scanner.com footer'
        expected_res = set([u'abc@w3af-scanner.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_extract_emails_number(self):
        input_str = u'header abc4def@w3af.com footer'
        expected_res = set([u'abc4def@w3af.com'])
        self.assertEqual(self.bp_inst._extract_emails(input_str),
                         expected_res)

    def test_regex_url_parse_blank(self):
        self.bp_inst._regex_url_parse('')
        self.assertEqual(self.bp_inst._re_urls, set())

    def test_regex_url_parse_full_url(self):
        input_str = u'header http://www.w3af.com/foo/bar/index.html footer'
        expected_urls = set([URL('http://www.w3af.com/foo/bar/index.html'), ])

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_regex_url_parse_relative_url_paths(self):
        input_str = u'header /foo/bar/index.html footer'
        expected_urls = set([URL('http://www.w3af.com/foo/bar/index.html'), ])

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_regex_url_parse_relative_url_slash_file(self):
        input_str = u'header /subscribe.jsp footer'
        expected_urls = set([URL('http://www.w3af.com/subscribe.jsp'), ])

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_regex_url_parse_relative_url_file_only(self):
        """
        Please note that the expected output in this case is an empty set,
        adding support to parse "files" is possible, but too greedy and
        leads to lots of "parser false positives".
        """
        input_str = u'header subscribe.jsp footer'
        expected_urls = set()

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_regex_url_parse_relative_url_a_tag(self):
        input_str = u'header <a href="/foo/bar/index.html">foo</a> footer'
        expected_urls = set([URL('http://www.w3af.com/foo/bar/index.html'), ])

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_regex_url_parse_relative_no_slash(self):
        input_str = u'header <a href="index">foo</a> footer'
        expected_urls = set()

        self.bp_inst._regex_url_parse(input_str)

        self.assertEqual(expected_urls, self.bp_inst._re_urls)

    def test_decode_url_simple(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        decoded_url = bp_inst._decode_url(u'http://www.w3af.com/index.html')
        self.assertEqual(decoded_url, u'http://www.w3af.com/index.html')

    def test_decode_url_url_encoded(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        decoded_url = bp_inst._decode_url(u'http://www.w3af.com/ind%E9x.html')
        self.assertEqual(decoded_url, u'http://www.w3af.com/ind\xe9x.html')

    def test_decode_url_skip_safe_chars(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        decoded_url = bp_inst._decode_url(
            u'http://w3af.com/search.php?a=%00x&b=2%20c=3%D1')
        self.assertEqual(
            decoded_url, u'http://w3af.com/search.php?a=%00x&b=2 c=3\xd1')

    def test_decode_url_ignore_errors(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'utf-8'

        decoded_url = bp_inst._decode_url(
            u'http://w3af.com/blah.jsp?p=SQU-300&bgc=%FFAAAA')
        self.assertEqual(
            decoded_url, u'http://w3af.com/blah.jsp?p=SQU-300&bgc=AAAA')
