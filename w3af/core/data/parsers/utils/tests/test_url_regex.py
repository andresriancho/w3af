# -*- coding: utf-8 -*-
"""
test_url_regex.py

Copyright 2019 Andres Riancho

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


from w3af.core.data.parsers.utils.url_regex import URL_RE, RELATIVE_URL_RE


class TestURLRegex(unittest.TestCase):
    def test_simple_domain(self):
        matches = URL_RE.findall('http://w3af.org/')
        self.assertEqual(matches[0][0], 'http://w3af.org/')

    def test_case_insensitive(self):
        matches = URL_RE.findall('hTTp://w3af.org/')
        self.assertEqual(matches[0][0], 'hTTp://w3af.org/')

    def test_simple_domain_padding(self):
        matches = URL_RE.findall('123 http://w3af.org/ 456')
        self.assertEqual(matches[0][0], 'http://w3af.org/')

    def test_domain_filename_padding(self):
        matches = URL_RE.findall('123 http://w3af.org/scanner 456')
        self.assertEqual(matches[0][0], 'http://w3af.org/scanner')

    def test_domain_filename_query_string_padding(self):
        matches = URL_RE.findall('123 http://w3af.org/scanner?id=1 456')
        self.assertEqual(matches[0][0], 'http://w3af.org/scanner?id=1')

    def test_domain_filename_query_string_multiple_params_padding(self):
        matches = URL_RE.findall('123 http://w3af.org/scanner?id=1&foo=bar 456')
        self.assertEqual(matches[0][0], 'http://w3af.org/scanner?id=1&foo=bar')

    def test_no_match_1(self):
        matches = URL_RE.findall('ftp://w3af.org')
        self.assertEqual(matches, [])

    def test_no_match_2(self):
        matches = URL_RE.findall('httt://w3af.org')
        self.assertEqual(matches, [])

    def test_no_match_3(self):
        matches = URL_RE.findall('http!://w3af.org')
        self.assertEqual(matches, [])

    def test_no_match_4(self):
        matches = URL_RE.findall('http:--w3af.org')
        self.assertEqual(matches, [])


class TestRelativeURLRegex(unittest.TestCase):
    def test_simple_filename(self):
        matches = RELATIVE_URL_RE.findall('/abc.html')
        self.assertEqual(matches[0][0], '/abc.html')

    @unittest.SkipTest
    def test_starts_without_slash(self):
        #
        # TODO: This is a bug!
        #
        #       Removing the SkipTest will show that the test is matching
        #       /def/123.html instead of the expected abd/def/123.html
        #
        #       The regular expression matches start with /
        #
        matches = RELATIVE_URL_RE.findall('abc/def/123.html')
        self.assertEqual(matches[0][0], 'abc/def/123.html')

    def test_with_padding(self):
        matches = RELATIVE_URL_RE.findall('123 /abc/def/123.html 456')
        self.assertEqual(matches[0][0], '/abc/def/123.html')

    def test_two_slashes(self):
        # This is filtered by ReExtract._filter_false_urls
        matches = RELATIVE_URL_RE.findall('//foo.123.html')
        self.assertEqual(matches[0][0], '//foo.123.html')

    def test_relative(self):
        matches = RELATIVE_URL_RE.findall('../../foobar/uploads/bar.html')
        self.assertEqual(matches[0][0], '/../foobar/uploads/bar.html')

    def test_query_string(self):
        matches = RELATIVE_URL_RE.findall('/foo.html?id=1')
        self.assertEqual(matches[0][0], '/foo.html?id=1')

    def test_path_query_string(self):
        matches = RELATIVE_URL_RE.findall('/abc/foo.html?id=1')
        self.assertEqual(matches[0][0], '/abc/foo.html?id=1')

    def test_path_query_string_multi(self):
        matches = RELATIVE_URL_RE.findall('/abc/foo.html?id=1&foo=1')
        self.assertEqual(matches[0][0], '/abc/foo.html?id=1&foo=1')

    def test_full_url(self):
        # This is filtered by ReExtract._filter_false_urls
        matches = RELATIVE_URL_RE.findall('http://w3af.org/foo.html')
        self.assertEqual(matches[0][0], '://w3af.org/foo.html')

    def test_with_fake_start(self):
        matches = RELATIVE_URL_RE.findall('</abc> /def.html')
        self.assertEqual(matches[0][0], '/def.html')

    def test_no_match_1(self):
        matches = RELATIVE_URL_RE.findall('/abc')
        self.assertEqual(matches, [])

    def test_no_match_2(self):
        matches = RELATIVE_URL_RE.findall('abc.html')
        self.assertEqual(matches, [])

